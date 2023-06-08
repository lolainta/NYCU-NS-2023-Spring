from mininet.topo import Topo


class NSCAP_hw7_1(Topo):
    def build(self):
        # Add hosts and switches
        h1 = self.addHost("h1", ip="10.0.0.1/24", mac="00:00:00:00:00:01")
        h2 = self.addHost("h2", ip="10.0.0.2/24", mac="00:00:00:00:00:02")
        h3 = self.addHost("h3", ip="10.0.0.3/24", mac="00:00:00:00:00:03")
        h4 = self.addHost("h4", ip="10.0.0.4/24", mac="00:00:00:00:00:04")
        sw = self.addSwitch("s1")

        # Add links
        self.addLink(sw, h1)
        self.addLink(sw, h2)
        self.addLink(sw, h3)
        self.addLink(sw, h4)


class NSCAP_hw7_2(Topo):
    def build(self):
        # Add hosts and switches
        h5 = self.addHost("h5", ip="10.0.0.5/24", mac="00:00:00:00:00:05")
        h6 = self.addHost("h6", ip="10.0.0.6/24", mac="00:00:00:00:00:06")
        h7 = self.addHost("h7", ip="10.0.0.7/24", mac="00:00:00:00:00:07")
        h8 = self.addHost("h8", ip="10.0.0.8/24", mac="00:00:00:00:00:08")
        sw = self.addSwitch("s2")

        # Add links
        self.addLink(sw, h5)
        self.addLink(sw, h6)
        self.addLink(sw, h7)
        self.addLink(sw, h8)


topos = {"VM1": (lambda: NSCAP_hw7_1()), "VM2": (lambda: NSCAP_hw7_1())}
