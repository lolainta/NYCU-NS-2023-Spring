from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls, CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, in_proto, ethernet, ether_types

FILTER_TABLE_1 = 5
FILTER_TABLE_2 = 10
FORWARD_TABLE = 15


class Switch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize mac address table.
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def add_default_table(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=0,
            instructions=[
                parser.OFPInstructionGotoTable(FILTER_TABLE_1),
            ],
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def add_filter_table_1(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=FILTER_TABLE_1,
            priority=20,
            match=parser.OFPMatch(
                eth_type=ether_types.ETH_TYPE_IP,
                ip_proto=in_proto.IPPROTO_ICMP,
            ),
            instructions=[
                parser.OFPInstructionGotoTable(FILTER_TABLE_2),
            ],
        )
        datapath.send_msg(mod)
        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=FILTER_TABLE_1,
            priority=10,
            instructions=[
                parser.OFPInstructionGotoTable(FORWARD_TABLE),
            ],
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def add_filter_table_2(self, ev):
        datapath = ev.msg.datapath
        parser = datapath.ofproto_parser
        for tp in [3, 4]:
            mod = parser.OFPFlowMod(
                datapath=datapath,
                table_id=FILTER_TABLE_2,
                priority=20,
                match=parser.OFPMatch(in_port=tp),
            )
            datapath.send_msg(mod)
        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=FILTER_TABLE_2,
            priority=10,
            instructions=[
                parser.OFPInstructionGotoTable(FORWARD_TABLE),
            ],
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def add_forward_table(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        mod = parser.OFPFlowMod(
            datapath=datapath,
            table_id=FORWARD_TABLE,
            priority=10,
            match=parser.OFPMatch(),
            instructions=[
                parser.OFPInstructionActions(
                    ofproto.OFPIT_APPLY_ACTIONS,
                    [
                        parser.OFPActionOutput(
                            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER
                        )
                    ],
                )
            ],
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # get Datapath ID to identify OpenFlow switches.
        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        # analyse the received packets using the packet library.
        pkt = packet.Packet(msg.data)
        eth_pkt = pkt.get_protocol(ethernet.ethernet)
        dst = eth_pkt.dst
        src = eth_pkt.src

        # get the received port number from packet_in message.
        in_port = msg.match["in_port"]

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        # if the destination mac address is already learned,
        # decide which port to output the packet, otherwise FLOOD.
        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # construct action list.
        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time.
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # construct packet_out message and send it.
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data,
        )
        datapath.send_msg(out)
