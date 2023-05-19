from struct import pack, unpack
from .helper import Pointer

class SimpleQUICException(Exception):
    pass

class Header:
    def __init__(self) -> None:
        self.header_form: int = 0 # 1 bit
        self.packet_type: int = 0 # 2 bits
        self.pkt_num_len: int = 0b11 # 2 bit
        self.version: int = 1 # 32 bits
        self.dst_id_len = 20 # 8 bits
        self.dst_id: int = 0 # 160 bits
        self.src_id_len: int = 20 # 8 bits
        self.src_id: int = 0 # 160 bits
        self.length: int = 0 # 62 bits
        self.pkt_num: int = 0 # 32 bits
        self.payload_len: int = 0

    def serialize(self):
        if self.header_form == 1:
            # long header
            first_byte = (self.header_form << 7) +\
                         (1 << 6) +\
                         (self.packet_type << 4) +\
                         self.pkt_num_len

            self.length = 4 + self.payload_len

            hdr = pack(f"!BLB{self.dst_id_len}sB{self.src_id_len}s8s{self.pkt_num_len+1}s",
                       first_byte,
                       self.version,
                       self.dst_id_len,
                       self.dst_id.to_bytes(self.dst_id_len, "big"),
                       self.src_id_len,
                       self.src_id.to_bytes(self.src_id_len, "big"),
                       (self.length | (0b11 << 62)).to_bytes(8, "big"),
                       self.pkt_num.to_bytes(self.pkt_num_len+1, "big"))

        elif self.header_form == 0:
            # short header
            first_byte = 0x40 + self.pkt_num_len

            hdr = pack(f"!B{self.dst_id_len}s{self.pkt_num_len+1}s",
                       first_byte,
                       self.dst_id.to_bytes(self.dst_id_len, "big"),
                       self.pkt_num.to_bytes(self.pkt_num_len+1, "big"))

        else:
            hdr = None

        return hdr

    def deserialize(self, pkt):
        ptr = Pointer()
        (first_byte, ) = unpack("!B", pkt[ptr+0:ptr+1])
        self.header_form = (first_byte & 0x80) >> 7
        if self.header_form == 1:
            # long header
            self.packet_type = (first_byte & 0x30) >> 4
            self.pkt_num_len = first_byte & 0x03

            self.version, self.dst_id_len, self.dst_id, self.src_id_len, self.src_id = unpack(
                    f"!LB{self.dst_id_len}sB{self.src_id_len}s",
                    pkt[ptr+0:ptr+(4+1+self.dst_id_len+1+self.src_id_len)]
                )
            assert self.dst_id_len == 20
            assert self.src_id_len == 20
            self.dst_id = int.from_bytes(self.dst_id, "big")
            self.src_id = int.from_bytes(self.src_id, "big")

            self.length, self.pkt_num = unpack(f"!8s{self.pkt_num_len+1}s", pkt[ptr+0:ptr+(8+self.pkt_num_len+1)])
            self.length = int.from_bytes(self.length, "big")
            self.length &= (~(0b11 << 62))
            self.pkt_num = int.from_bytes(self.pkt_num, "big")

        elif self.header_form == 0:
            # short header
            self.pkt_num_len = first_byte & 0x03
            assert self.dst_id_len == 20
            (self.dst_id, self.pkt_num) = unpack(
                f"!{self.dst_id_len}s{self.pkt_num_len+1}s",
                pkt[ptr+0:ptr+(self.dst_id_len+self.pkt_num_len+1)])
            self.dst_id = int.from_bytes(self.dst_id, "big")
            self.pkt_num = int.from_bytes(self.pkt_num, "big")
        
        return ptr.v

    def clear(self):
        self.__init__()

    def __repr__(self) -> str:
        return_str = ""
        if self.header_form == 1:
            return_str += "long header"
            if self.packet_type == 0x00:
                return_str += ", init packet"
            return_str += f", dst_id={self.dst_id}, src_id={self.src_id}, pkt_num={self.pkt_num}"
        elif self.header_form == 0:
            return_str += f"short header, dst_id={self.dst_id}, pkt_num={self.pkt_num}"
        return return_str

class Frame:
    PADDING = 0x00
    PING = 0x01
    ACK = 0x02
    STREAM = 0x08 | 0x04 | 0x02
    FIN = 0x01
    MAX_DATA = 0x10
    DATA_BLOCKED = 0x14
    CONNECTION_CLOSE = 0x1c
    HANDSHAKE_DONE = 0x1e

    PKT_NUM_LEN = 0b11
    STREAM_ID_LEN = 8
    OFFSET_LEN = 8
    LENGTH_LEN = 8

    def __init__(self) -> None:
        self.type = None
        self.largest_ack = None
        self.ack_delay = 0
        self.ack_range_count = 0
        self.first_ack_range = 0
        self.ack_range = 0
        self.stream_id = None
        self.offset = None
        self.length = None
        self.stream_data = None
        self.max_data = None
        self.error_code = None
        self.frame_type = None
        self.reason_phrase_len = None
        self.reason_phrase = None
        self.directional = 0x00

    def serialize(self):
        if self.type == Frame.PADDING or self.type == Frame.PING or self.type == Frame.HANDSHAKE_DONE:
            body = pack("!B", self.type)
        elif self.type == Frame.ACK:
            body = pack(f"!B{Frame.PKT_NUM_LEN+1}sBB{Frame.PKT_NUM_LEN+1}s",
                        self.type,
                        self.largest_ack.to_bytes(Frame.PKT_NUM_LEN+1, "big"),
                        self.ack_delay,
                        self.ack_range_count,
                        self.first_ack_range.to_bytes(Frame.PKT_NUM_LEN+1, "big"))
        elif self.type == Frame.STREAM or self.type == Frame.STREAM | Frame.FIN:
            body = pack(f"!B{Frame.STREAM_ID_LEN}s{Frame.OFFSET_LEN}s{Frame.LENGTH_LEN}s",
                        self.type,
                        (self.stream_id | (self.directional << 62)).to_bytes(Frame.STREAM_ID_LEN, "big"),
                        self.offset.to_bytes(Frame.OFFSET_LEN, "big"),
                        self.length.to_bytes(Frame.LENGTH_LEN, "big"))
            body += self.stream_data
        elif self.type == Frame.MAX_DATA or self.type == Frame.DATA_BLOCKED:
            body = pack(f"!B8s", self.type, self.max_data.to_bytes(8, "big"))
        elif self.type == Frame.CONNECTION_CLOSE:
            body = pack(f"!B8sB8s{self.reason_phrase_len}s",
                        self.type,
                        self.error_code.to_bytes(8, "big"),
                        self.frame_type,
                        self.reason_phrase_len.to_bytes(8, "big"),
                        bytes(self.reason_phrase))

        return body

    def deserialize(self, pkt):
        ptr = Pointer()
        (self.type, ) = unpack("!B", pkt[ptr+0:ptr+1])
        if self.type == Frame.ACK:
            (self.largest_ack,
            self.ack_delay,
            self.ack_range_count,
            self.first_ack_range) = unpack(f"!{Frame.PKT_NUM_LEN+1}sBB{Frame.PKT_NUM_LEN+1}s", pkt[ptr+0:])

            self.largest_ack = int.from_bytes(self.largest_ack, "big")
            self.first_ack_range = int.from_bytes(self.first_ack_range, "big")

        elif self.type == Frame.STREAM or self.type == Frame.STREAM | Frame.FIN:
            (stream_id,
            self.offset,
            self.length) = unpack(f"!{Frame.STREAM_ID_LEN}s{Frame.OFFSET_LEN}s{Frame.LENGTH_LEN}s", pkt[ptr+0:ptr+(Frame.STREAM_ID_LEN+Frame.OFFSET_LEN+Frame.LENGTH_LEN)])

            stream_id = int.from_bytes(stream_id, "big")
            self.stream_id = stream_id & (~(3 << 62))
            self.offset = int.from_bytes(self.offset, "big")
            self.length = int.from_bytes(self.length, "big")

            self.stream_data = pkt[ptr+0:]

        elif self.type == Frame.MAX_DATA or self.type == Frame.DATA_BLOCKED:
            (self.max_data, ) = unpack("!8s", pkt[ptr+0:])
            self.max_data = int.from_bytes(self.max_data, "big")

        elif self.type == Frame.CONNECTION_CLOSE:
            (self.error_code,
            self.frame_type,
            self.reason_phrase_len) = unpack("!8sB8s", pkt[ptr+0:ptr+(8+1+8)])

            self.error_code = int.from_bytes(self.error_code, "big")
            self.reason_phrase_len = int.from_bytes(self.reason_phrase_len, "big")

            (self.reason_phrase, ) = unpack(f"!{self.reason_phrase_len}s", pkt[ptr+0:])
            self.reason_phrase = self.reason_phrase.decode("utf-8")

    def clear(self):
        self.__init__()

    def __repr__(self) -> str:
        r_str = ""
        if self.type == Frame.ACK:
            r_str += f", ACK, largest_ack={self.largest_ack} {self.first_ack_range=}"
        elif self.type == Frame.MAX_DATA:
            r_str += f", MAX_DATA, max_data={self.max_data}"
        elif self.type == Frame.STREAM:
            r_str += f", STREAM, {self.stream_id=}, {self.offset=}, {self.length=}"
        elif self.type == Frame.STREAM | Frame.FIN:
            r_str += f", STREAM, FIN, {self.stream_id=}, {self.offset=}, {self.length=}"
        elif self.type == Frame.HANDSHAKE_DONE:
            r_str += f", HANDSHAKE_DONE"
        return r_str

class Packet:
    def __init__(self, hdr=None, frm=None) -> None:
        if not hdr:
            hdr = Header()
        if not frm:
            frm = Frame()
        self.header = hdr
        self.frame = frm

    def serialize(self):
        return self.header.serialize() + self.frame.serialize()

    def deserialize(self, pkt):
        self.clear()
        header_end = self.header.deserialize(pkt)
        self.frame.deserialize(pkt[header_end:])

    def clear(self):
        self.header.clear()
        self.frame.clear()

    def __repr__(self) -> str:
        return str(self.header) + str(self.frame)