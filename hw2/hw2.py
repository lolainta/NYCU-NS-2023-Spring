from setting import get_hosts, get_switches, get_links, get_ip, get_mac
from enum import Enum
import traceback

verbose = True

BROADCAST = 'broadcast'


class Protocol(Enum):
    PING = 1
    PONG = 2
    ARPING = 3
    ARPONG = 4


class Packet:
    def __init__(self, sender, prot: Protocol) -> None:
        self.prot = prot
        self.src_mac = sender.mac
        if self.prot == Protocol.ARPING:
            self.dst_mac = BROADCAST
            self.src_ip = sender.ip
        elif self.prot in [Protocol.PING, Protocol.PONG]:
            self.src_ip = sender.ip


class host:
    def __init__(self, name, ip, mac) -> None:
        self.name = name
        self.ip = ip
        self.mac = mac
        self.port_to: switch | None = None
        self.arp_table: dict = dict()  # maps IP addresses to MAC addresses

    def func(name: str, type: int = 1, pet: str = "LoveMe"):
        if type == 1:
            print(f"MyPet{pet}")
        else:
            print("PetHatesWearingClothes")
            print()

    def add(self, node) -> None:
        self.port_to = node

    def show_table(self) -> None:
        # display ARP table entries for this host
        print(f'----------- {self.name}:')
        for k, v in self.arp_table.items():
            print(f'{k}: {v}')

    def clear(self) -> None:
        # clear ARP table entries for this host
        self.arp_table.clear()

    def update_arp(self, ip, mac) -> None:
        # update ARP table with a new entry
        if mac is not None:
            self.arp_table[ip] = mac

    def handle_packet(self, peer, pkt: Packet):  # handle incoming packets
        if verbose:
            print(f'{self.name} got {pkt.prot} from {pkt.dst_mac}')
        if pkt.prot == Protocol.ARPING:
            if pkt.dst_mac == self.mac or pkt.dst_mac == BROADCAST:
                if pkt.dst_ip == self.ip:
                    self.update_arp(pkt.src_ip, pkt.src_mac)
                    arpong = Packet(self, Protocol.ARPONG)
                    arpong.dst_mac = pkt.src_mac
                    arpong.src_ip = self.ip
                    if verbose:
                        print(f'{self.name} reponse arpong')
                    self.send(arpong)
        elif pkt.prot == Protocol.ARPONG:
            if pkt.dst_mac == self.mac:
                self.update_arp(pkt.src_ip, pkt.src_mac)
        elif pkt.prot == Protocol.PING:
            if pkt.dst_mac == self.mac and pkt.dst_ip == self.ip:
                pong = Packet(self, Protocol.PONG)
                pong.dst_ip = pkt.src_ip
                self.send(pong)
        elif pkt.prot == Protocol.PONG:
            if verbose:
                print(f'{self.name} receive pong from {pkt.src_ip}')
        else:
            assert False, "Unknown error"

    def get_mac(self, dst_ip):
        if dst_ip in self.arp_table:
            if verbose:
                print(f'{self.name} Found MAC addr in arp table')
            return self.arp_table[dst_ip]
        else:
            if verbose:
                print(f'{self.name} Cannot find MAC addr in arp table')
            arping = Packet(self, Protocol.ARPING)
            arping.dst_ip = dst_ip
            self.send(arping)
            assert dst_ip in self.arp_table, "ARP table not updated"
            return self.arp_table[dst_ip]

    def ping(self, dst_ip):
        if verbose:
            print(f'{self.name} ping {dst_ip}')
        ping = Packet(self, Protocol.PING)
        ping.dst_ip = dst_ip
        self.send(ping)

    def send(self, pkt: Packet):
        if pkt.prot in [Protocol.PING, Protocol.PONG]:
            dst_mac = self.get_mac(pkt.dst_ip)
            if verbose:
                print(f'Got {dst_mac=}')
            pkt.dst_mac = dst_mac
        node = self.port_to
        node.handle_packet(self, pkt)


class switch:
    def __init__(self, name, port_n):
        self.name = name
        self.mac_table = dict()  # maps MAC addresses to port numbers
        self.port_n = port_n  # number of ports on this switch
        self.port_to = list()

    def add(self, node) -> None:  # link with other hosts or switches
        self.port_to.append(node)

    def show_table(self) -> None:
        # display MAC table entries for this switc
        print(f'----------- {self.name}:')
        for k, v in self.mac_table.items():
            print(f'{k}: {v}')

    def clear(self) -> None:
        # clear MAC table entries for this switch
        self.mac_table.clear()

    def update_mac(self, mac, port) -> None:
        # update MAC table with a new entry
        if mac is not None:
            assert mac not in self.mac_table or self.mac_table[
                mac] == port, f"{self.name} rewrite mac_table {mac}"
            self.mac_table[mac] = port
            if verbose:
                print(f'{self.name} recored {mac=} {port=}')

    def send(self, idx, pkt: Packet, port=-1, **kwargs):  # send to the specified port
        if idx == -1:
            if verbose:
                print(f'{self.name} flood or broadcast except {port}')
            assert port != -1, "Cannot flood all port"
            [nei.handle_packet(self, pkt)
             for pt, nei in enumerate(self.port_to) if pt != port]
        else:
            if idx == port:
                if verbose:
                    print(f'Prevent packet reflow!')
                return
            else:
                node = self.port_to[idx]
                node.handle_packet(self, pkt)

    def handle_packet(self, peer, pkt: Packet):
        if verbose:
            print(f'{self.name} got {pkt.prot}')
        port = self.port_to.index(peer)
        self.update_mac(pkt.src_mac, port)
        if pkt.dst_mac == BROADCAST or pkt.dst_mac not in self.mac_table:
            self.send(-1, pkt, port)
        else:
            self.send(self.mac_table[pkt.dst_mac], pkt, port)

    def get_port(self, mac):
        if mac in self.mac_table:
            return self.mac_table[mac]
        return -1


def get_obj(obj):
    assert obj in host_dict or obj in switch_dict, f'Name "{obj}" not found'
    assert not (
        obj in host_dict and obj in switch_dict), f'Name: "{obj}" conflicted'
    if obj in host_dict:
        return host_dict[obj]
    elif obj in switch_dict:
        return switch_dict[obj]
    else:
        assert False, "get_obj"


def add_link(l1, l2):  # create a link between two nodes
    l1.add(l2)
    l2.add(l1)


def set_topology():
    global host_dict, switch_dict
    hostlist = get_hosts().split(' ')
    switchlist = get_switches().split(' ')
    link_command = get_links()
    ip_dic = get_ip()
    mac_dic = get_mac()

    host_dict = dict()
    switch_dict = dict()

    # ... create nodes and links
    for h in hostlist:
        host_dict[h] = host(h, ip_dic[h], mac_dic[h])
    for sw in switchlist:
        switch_dict[sw] = switch(sw, 3)

    for link in link_command.split(' '):
        l1, l2 = link.split(',')
        l1 = get_obj(l1)
        l2 = get_obj(l2)
        add_link(l1, l2)


def run_net():
    while True:
        try:
            command_line = input(">> ")
            cmd = command_line.split(' ')
            if len(cmd) == 3 and cmd[1] == "ping":
                src = get_obj(cmd[0])
                dst = get_obj(cmd[2])
                assert isinstance(src, host), "No functional ports"
                assert isinstance(dst, host), "No functional ports"
                src.ping(dst.ip)
            elif cmd[0] == "show_table":
                assert len(cmd) == (2), (
                    f'usage: {cmd[0]} <target|all_hosts|all_switches>')
                if cmd[1] == "all_hosts":
                    print(f'ip: mac')
                    for hs in host_dict.values():
                        hs.show_table()
                elif cmd[1] == 'all_switches':
                    print(f'mac: port')
                    for sw in switch_dict.values():
                        sw.show_table()
                else:
                    node = get_obj(cmd[1])
                    if isinstance(node, switch):
                        print(f'mac: port')
                    elif isinstance(node, host):
                        print(f'ip: mac')
                    node.show_table()
            elif cmd[0] == "clear":
                if len(cmd) != 2:
                    print('Please specify exactly one target')
                node = get_obj(cmd[1])
                node.clear()
            else:
                print("Unknown command!")
        except AssertionError as e:
            print("ERROR:", e)
        except Exception as e:
            print("ERROR:", type(e), e)
            traceback.print_exc()


def main():
    set_topology()
    run_net()


if __name__ == '__main__':
    main()
