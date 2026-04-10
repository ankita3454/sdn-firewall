from mininet.topo import Topo

class FirewallTopo(Topo):
    def build(self):
        # Create 1 switch
        s1 = self.addSwitch('s1')

        # Create 3 hosts with specific IPs
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')

        # Link them all to the single switch
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)

topos = { 'firewalltopo': (lambda: FirewallTopo()) }
