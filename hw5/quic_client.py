from quic import QUIC
from packet import Packet, SYN, SYNACK
from time import sleep
from states import ClientState
import pickle


class QUICClient(QUIC):
    def __init__(self) -> None:
        super().__init__()
        self.seq = 0
        self.ack = 0
        self.state = ClientState.IDLE
        self.server = None

    def connect(self, socket_addr: tuple[str, int]):
        while True:
            match self.state:
                case ClientState.IDLE:
                    pkt = SYN(self.seq, self.ack)
                    self.sock.sendto(pkt.serialize(), socket_addr)
                    self.seq += len(pkt)
                    self.state = ClientState.SYN_SENT
                case ClientState.SYN_SENT:
                    data, addr = self.get_data("SYNACK")
                    if data == None:
                        self.state = ClientState.IDLE
                    else:
                        if addr != socket_addr:
                            print(f"ERROR: {addr} != {socket_addr}")
                        if not isinstance(data, SYNACK):
                            print(f"ERROR: SYNACK expected, got {data}")
                        self.server = addr
                        print(f"ESTABLISHED with {self.server}")
                        return
                case _:
                    assert False, "Unknown State"

    def send(self, stream_id: int, data: bytes):
        """call this method to send data, with non-reputation stream_id"""
        pass

    def recv(self) -> tuple[int, bytes]:
        """receive a stream, with stream_id"""
        return (1, b"abc123")

    def close(self):
        """close the connection and the socket"""
        pass
