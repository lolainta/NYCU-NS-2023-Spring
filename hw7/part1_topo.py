from mininet.topo import Topo


class NSCAP_HW7(Topo):
    def build(self):
        # Add hosts and switches
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")
        h3 = self.addHost("h3")
        h4 = self.addHost("h4")
        sw = self.addSwitch("s1")

        # Add links
        self.addLink(sw, h1)
        self.addLink(sw, h2)
        self.addLink(sw, h3)
        self.addLink(sw, h4)


topos = {"part1": (lambda: NSCAP_HW7())}
