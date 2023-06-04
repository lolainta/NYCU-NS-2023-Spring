from mininet.topo import Topo


class NSCAP_HW7(Topo):
    def build(self):
        # Add hosts and switches
        h5 = self.addHost("h5", ip="10.0.0.5")
        h6 = self.addHost("h6", ip="10.0.0.6")
        h7 = self.addHost("h7", ip="10.0.0.7")
        h8 = self.addHost("h8", ip="10.0.0.8")
        sw = self.addSwitch("s2")

        # Add links
        self.addLink(sw, h5)
        self.addLink(sw, h6)
        self.addLink(sw, h7)
        self.addLink(sw, h8)


topos = {"VM2": (lambda: NSCAP_HW7())}
