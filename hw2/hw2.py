from setting import get_hosts, get_switches, get_links, get_ip, get_mac
from enum import Enum
import traceback


class Pkt(Enum):
    PING = 1
    PONG = 2
    ARP = 3


class host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac
        self.port_to: switch | None = None
        self.arp_table: dict = dict()  # maps IP addresses to MAC addresses

    def add(self, node) -> None:
        self.port_to = node

    def show_table(self):
        # display ARP table entries for this host
        print(f'{self.name} ARP table')
        for k, v in self.arp_table.items():
            print(k, v)

    def clear(self):
        # clear ARP table entries for this host
        self.arp_table.clear()

    def update_arp(self, ip, mac):
        # update ARP table with a new entry
        if mac is not None:
            self.arp_table[ip] = mac

    def handle_packet(self, peer, tp: Pkt, **kwargs):  # handle incoming packets
        print(f'{self.name} got {tp}')
        match tp:
            case Pkt.PING:
                raise Exception("Not implemented yet")
            case Pkt.PONG:
                raise Exception("Not implemented yet")
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

        pong = self.send(Pkt.PING, dst_ip, dst_mac)
        # node = self.port_to
        # pong = node.handle_packet(self, Pkt.PING, self.mac, dst_mac)
        print(pong)

    def send(self, tp, dst_ip, dst_mac):
        node = self.port_to
        return node.handle_packet(self, tp, self.mac, dst_mac)


class switch:
    def __init__(self, name, port_n):
        self.name = name
        self.mac_table = dict()  # maps MAC addresses to port numbers
        self.port_n = port_n  # number of ports on this switch
        self.port_to = list()

    def add(self, node):  # link with other hosts or switches
        self.port_to.append(node)

    def show_table(self):
        # display MAC table entries for this switc
        print(f'{self.name} mac table')
        for k, v in self.mac_table.items():
            print(k, v)

    def clear(self):
        # clear MAC table entries for this switch
        self.mac_table.clear()

    def update_mac(self, mac, port):
        # update MAC table with a new entry
        if mac is not None:
            assert mac not in self.mac_table or self.mac_table[mac] == port
            self.mac_table[mac] = port
    """
    def send(self, idx, ...): # send to the specified port
        node = self.port_to[idx] 
        node.handle_packet(...) 
    """

    def handle_packet(self, peer, tp: Pkt, **kwargs):
        port = self.port_to.index(peer)
        print(f'{self.name} got {tp}')
        match tp:
            case Pkt.ARP:
                src_mac = kwargs['src_mac']
                target_ip = kwargs['target_ip']
                self.update_mac(src_mac, port)
                # self.show_table()
                ret = None
                for pt, nei in enumerate(self.port_to):
                    if pt != port:
                        ans = nei.handle_packet(
                            self, tp, src_mac=src_mac, target_ip=target_ip)
                        self.update_mac(ans, pt)
                        if ans is not None:
                            assert ret is None
                            ret = ans
                return ret
            case Pkt.PING:
                raise Exception("Not implemented yet")
            case Pkt.PONG:
                raise Exception("Not implemented yet")
            case _:
                raise Exception("Not implemented yet")


def get_obj(obj):
    assert obj in host_dict or obj in switch_dict, f'Name "{obj}" not found'
    assert not (
        obj in host_dict and obj in switch_dict), f'Name: "{obj}" conflicted'
    if obj in host_dict:
        return host_dict[obj]
    elif obj in switch_dict:
        return switch_dict[obj]
    else:
        assert False


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

    host_dict = dict()  # maps host names to host objects
    switch_dict = dict()  # maps switch names to switch objects

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


def ping(tmp1, tmp2):  # initiate a ping between two hosts
    global host_dict, switch_dict
    if tmp1 in host_dict and tmp2 in host_dict:
        node1 = host_dict[tmp1]
        node2 = host_dict[tmp2]
        node1.ping(node2.ip)
    else:
        pass
        # invalid command


def show_table(node: host | switch):  # display the ARP or MAC table of a node
    node.show_table()
    pass


def clear():
    pass
    # ...


def run_net():
    while (1):
        try:
            command_line = input(">> ")
            # ... handle user commands
            cmd = command_line.split(' ')
            if len(cmd) == 3 and cmd[1] == "ping":
                src = get_obj(cmd[0])
                dst = get_obj(cmd[2])
                if not isinstance(src, host) or not isinstance(dst, host):
                    print("No funcitonal ports")
                    continue
                src.ping(dst.ip)
            elif cmd[0] == "show_table":
                node = get_obj(cmd[1])
                show_table(node)
                print(cmd, "show table not implemeted")
            elif cmd[0] == "clear":
                clear()
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
