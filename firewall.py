from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.packet.ethernet import ethernet
from pox.lib.addresses import IPAddr

log = core.getLogger()

class Firewall(object):
    def __init__(self, connection):
        self.connection = connection
        connection.addListeners(self)
        self.mac_to_port = {}

    def _handle_PacketIn(self, event):
        packet = event.parsed
        if not packet.parsed:
            return

        packet_in = event.ofp # The raw OpenFlow packet

        # --------------------------------------------------------
        # 1. FIREWALL LOGIC (IP Filtering)
        # --------------------------------------------------------
        if packet.type == ethernet.IP_TYPE:
            ipv4_packet = packet.payload
            src_ip = ipv4_packet.srcip
            dst_ip = ipv4_packet.dstip

            if src_ip == IPAddr('10.0.0.1') and dst_ip == IPAddr('10.0.0.3'):
                log.info("FIREWALL TRIGGERED: Dropping %s -> %s", src_ip, dst_ip)
                
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match.from_packet(packet, event.port)
                msg.idle_timeout = 60
                msg.hard_timeout = 120
                msg.buffer_id = packet_in.buffer_id
                # No actions = DROP
                self.connection.send(msg)
                return

        # --------------------------------------------------------
        # 2. NORMAL L2 LEARNING SWITCH LOGIC
        # --------------------------------------------------------
        # Learn the source port
        self.mac_to_port[packet.src] = event.port

        if packet.dst in self.mac_to_port:
            # We know where this MAC address lives. Install a rule and forward.
            out_port = self.mac_to_port[packet.dst]
            
            log.info("Known destination. Installing flow: %s to port %i", packet.dst, out_port)
            
            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, event.port)
            msg.idle_timeout = 10  # Added timeouts to keep the switch fresh
            msg.hard_timeout = 30
            msg.actions.append(of.ofp_action_output(port=out_port))
            
            # THE FIX: Explicitly attach the packet data instead of using buffer_id
            msg.data = event.ofp 
            
            self.connection.send(msg)
        else:
            # We don't know where this MAC is (like an ARP broadcast). Flood it!
            log.info("Unknown destination %s. Flooding...", packet.dst)
            
            msg = of.ofp_packet_out()
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.data = packet_in
            msg.in_port = event.port
            self.connection.send(msg)

def launch():
    def start_switch(event):
        log.info("Switch Connected: %s" % (event.connection,))
        Firewall(event.connection)
    
    core.openflow.addListenerByName("ConnectionUp", start_switch)