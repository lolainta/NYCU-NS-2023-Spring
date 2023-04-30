from RDT import RDT
from packet import SYN
from time import sleep
from states import ClientState
import pickle
from threading import Thread


class QUICClient(RDT):
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
        if data.seq == -1:
            assert False, "Server Not Alive"
        print(f"ESTABLISHED Connection with server, window size = {data.rwnd}")
        self.peer = addr
        self.sender = Thread(target=self.sender_func, args=(data.rwnd,))
        self.sender.start()
        self.receiver.start()

    def send(self, stream_id: int, data: bytes):
        super().send(stream_id, data)

    def recv(self) -> tuple[int, bytes]:
        return super().recv()

    def close(self):
        super().close()
