from setting import get_hosts, get_switches, get_links, get_ip, get_mac

class host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac 
        self.port_to = None 
        self.arp_table = dict() # maps IP addresses to MAC addresses
    def add(self, node):
        self.port_to = node
    def show_table(self):
        # display ARP table entries for this host
    def clear(self):
        # clear ARP table entries for this host
    def update_arp(self, ...):
        # update ARP table with a new entry
    def handle_packet(self, ...): # handle incoming packets
        # ...
    def ping(self, dst_ip, ...): # handle a ping request
        # ...
    def send(self, ...):
        node = self.port_to # get node connected to this host
        node.handle_packet(...) # send packet to the connected node

class switch:
    def __init__(self, name, port_n):
        self.name = name
        self.mac_table = dict() # maps MAC addresses to port numbers
        self.port_n = port_n # number of ports on this switch
        self.port_to = list() 
    def add(self, node): # link with other hosts or switches
        self.port_to.append(node)
    def show_table(self):
        # display MAC table entries for this switch
    def clear(self):
        # clear MAC table entries for this switch
    def update_mac(self, ...):
        # update MAC table with a new entry
    def send(self, idx, ...): # send to the specified port
        node = self.port_to[idx] 
        node.handle_packet(...) 
    def handle_packet(self, ...): # handle incoming packets
        # ...


def add_link(tmp1, tmp2): # create a link between two nodes
    # ...

def set_topology():
    global host_dict, switch_dict
    hostlist = get_hosts().split(' ')
    switchlist = get_switches().split(' ')
    link_command = get_links()
    ip_dic = get_ip()
    mac_dic = get_mac()
    
    host_dict = dict() # maps host names to host objects
    switch_dict = dict() # maps switch names to switch objects
    
    # ... create nodes and links

def ping(tmp1, tmp2): # initiate a ping between two hosts
    global host_dict, switch_dict
    if tmp1 in host_dict and tmp2 in host_dict : 
        node1 = host_dict[tmp1]
        node2 = host_dict[tmp2]
        node1.ping(node2.ip)
    else : 
        # invalid command


def show_table(tmp): # display the ARP or MAC table of a node
    # ...


def clear():
    # ...


def run_net():
    while(1):
        command_line = input(">> ")
        # ... handle user commands

    
def main():
    set_topology()
    run_net()


if __name__ == '__main__':
    main()
