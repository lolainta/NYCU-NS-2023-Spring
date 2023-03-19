from setting import get_hosts, get_switches, get_links, get_ip, get_mac
from enum import Enum
import traceback


class Pkt(Enum):
    ICMP = 1
    ARP = 2


class host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.port_to: switch | None = None
        self.arp_table: dict = dict()  # maps IP addresses to MAC addresses

    def add(self, node) -> None:
        self.port_to = node

    def show_table(self) -> None:
        # display ARP table entries for this host
        print(f'ip: mac ----------- {self.name} ARP table:')
        for k, v in self.arp_table.items():
            print(f'{k}: {v}')

    def clear(self) -> None:
        # clear ARP table entries for this host
        self.arp_table.clear()

    def update_arp(self, ip, mac) -> None:
        # update ARP table with a new entry
        if mac is not None:
            self.arp_table[ip] = mac

    def handle_packet(self, peer, tp: Pkt, **kwargs):  # handle incoming packets
        print(f'{self.name} got {tp}')
        match tp:
            case Pkt.ICMP:
                src_mac = kwargs['src_mac']
                src_ip = kwargs['src_ip']
                self.update_arp(src_ip, src_mac)
                dst_ip = kwargs['dst_ip']
                dst_mac = kwargs['dst_mac']
                if dst_ip == self.ip and dst_mac == self.mac:
                    return (self.mac, self.ip)
                print(f"{self.name} discard {tp}")
                return None
            case Pkt.ARP:
                target_ip = kwargs['target_ip']
                if target_ip == self.ip:
                    print(f'{self.name} reply arp')
                    return self.mac
                else:
                    return None
            case _:
                raise Exception("Unknown packet type")

    def get_mac(self, dst_ip):
        if dst_ip in self.arp_table:
            print(f'{self.name} Found MAC addr in arp table')
            return self.arp_table[dst_ip]
        else:
            print(f'{self.name} Cannot find MAC addr in arp table')
            node = self.port_to
            mac = node.handle_packet(
                self, Pkt.ARP, src_mac=self.mac, target_ip=dst_ip)
            self.update_arp(dst_ip, mac)
            return mac

    def ping(self, dst_ip):
        print(f'{self.name} ping {dst_ip}')
        dst_mac = self.get_mac(dst_ip)
        print(f'Got {dst_mac=}')

        pong = self.send(Pkt.ICMP, dst_ip, dst_mac)
        print(pong)

    def send(self, tp, dst_ip, dst_mac):
        node = self.port_to
        return node.handle_packet(self, tp, src_ip=self.ip, src_mac=self.mac, dst_ip=dst_ip, dst_mac=dst_mac)


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
        print(f'mac: port ----------- {self.name} MAC table:')
        for k, v in self.mac_table.items():
            print(f'{k}: {v}')

    def clear(self) -> None:
        # clear MAC table entries for this switch
        self.mac_table.clear()

    def update_mac(self, mac, port) -> None:
        # update MAC table with a new entry
        if mac is not None:
            assert mac not in self.mac_table or self.mac_table[mac] == port
            self.mac_table[mac] = port

    def send(self, idx, tp, port=-1, **kwargs):  # send to the specified port
        if idx == -1:
            print(f'{self.name} flood except {port}')
            ret = [(pt, mac) for pt, mac in [(pt, nei.handle_packet(self, tp, **kwargs))
                                             for pt, nei in enumerate(self.port_to) if pt != port] if mac is not None]
            assert len(
                ret) < 2, f'Two respone {ret} when flood, (Maybe IP conflict or MAC conflicted)'
            for pt, mac in ret:
                self.update_mac(mac, pt)
            return ret[0][1] if ret else None
        else:
            node = self.port_to[idx]
            return node.handle_packet(self, tp, **kwargs)

    def handle_packet(self, peer, tp: Pkt, **kwargs):
        print(f'{self.name} got {tp}')
        port = self.port_to.index(peer)
        src_mac = kwargs['src_mac']
        self.update_mac(src_mac, port)
        match tp:
            case Pkt.ARP:
                target_ip = kwargs['target_ip']
                ret = self.send(-1, tp, port, src_mac=src_mac,
                                target_ip=target_ip)
                return ret
            case Pkt.ICMP:
                dst_mac = kwargs['dst_mac']
                dst_port = self.get_port(dst_mac)
                print(f'{self.name} {dst_mac} {dst_port}')
                pong = self.send(dst_port, tp, port=port, **kwargs)
                print(f'{pong=}')
                if pong:
                    self.update_mac(pong[0], dst_port)
                    return pong
                return None
            case _:
                raise Exception("Unknown packet type")

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
                    for hs in host_dict.values():
                        hs.show_table()
                elif cmd[1] == 'all_switches':
                    for sw in switch_dict.values():
                        sw.show_table()
                else:
                    node = get_obj(cmd[1])
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
