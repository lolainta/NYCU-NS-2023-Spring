from mininet.topo import Topo


class NSCAP_HW7(Topo):
    def build(self):
        # Add hosts and switches
        h1 = self.addHost("h1", ip="10.0.0.1", mac="00:00:00:00:00:01")
        h2 = self.addHost("h2", ip="10.0.0.2", mac="00:00:00:00:00:02")
        h3 = self.addHost("h3", ip="10.0.0.3", mac="00:00:00:00:00:03")
        h4 = self.addHost("h4", ip="10.0.0.4", mac="00:00:00:00:00:04")
        sw = self.addSwitch("s1")

        # Add links
        self.addLink(sw, h1)
        self.addLink(sw, h2)
        self.addLink(sw, h3)
        self.addLink(sw, h4)


topos = {"VM1": (lambda: NSCAP_HW7())}
