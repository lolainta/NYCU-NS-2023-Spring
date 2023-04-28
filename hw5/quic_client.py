from quic import QUIC
from packet import Packet, SYN, SYNACK, Stream
from time import sleep
from states import ClientState
import pickle


class QUICClient(QUIC):
    def __init__(self) -> None:
        super().__init__()
        self.state = ClientState.IDLE
        self.streams = dict()

    def connect(self, socket_addr: tuple[str, int]):
        for i in range(self.factor):
            pkt = SYN(self.rwnd)
            self.sock.sendto(pkt.serialize(), socket_addr)
            sleep(1 / self.factor)
        data, addr = self.get_data()
        self.server = addr
        if data is None:
            assert False, "Server Not Alive"
        print("ESTABLISHED Connection with server")
        self.sender.start()
        self.receiver.start()

    def send(self, stream_id: int, data: bytes):
        super().send(stream_id, data, self.server)

    def recv(self) -> tuple[int, bytes]:
        return super().recv()

    def close(self):
        super().close()
