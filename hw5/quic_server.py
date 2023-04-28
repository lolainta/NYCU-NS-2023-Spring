from quic import QUIC
from packet import Packet, SYN, SYNACK
import pickle
from states import ServerState
from time import sleep
from threading import Thread


class QUICServer(QUIC):
    def __init__(self) -> None:
        super().__init__()
        self.state = ServerState.IDLE
        self.verbose = True

    def listen(self, socket_addr: tuple[str, int]):
        self.sock.bind(socket_addr)
        pass

    def accept(self):
        data, addr = self.get_data("SYN")
        while data is None:
            data, addr = self.get_data("SYN")
        self.client = addr
        for i in range(self.factor):
            self.sock.sendto(SYNACK(self.rwnd, data).serialize(), self.client)
            sleep(1 / self.factor)
        print(f"ESTABLISHED Client {addr=}")
        self.state = ServerState.ESTABLISHED
        self.sender.start()
        self.receiver.start()

    def send(self, stream_id: int, data: bytes):
        super().send(stream_id, data, self.client)

    def recv(self) -> tuple[int, bytes]:
        return super().recv()

    def close(self):
        super().close()
