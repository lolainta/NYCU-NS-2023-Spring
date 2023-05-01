from RDT import RDT
from packet import SYNACK, SYN
from states import ServerState
from time import sleep
from threading import Thread


class QUICServer(RDT):
    def __init__(self) -> None:
        super().__init__()
        self.state = ServerState.IDLE
        # self.verbose = True

    def listen(self, socket_addr: tuple[str, int]):
        self.sock.bind(socket_addr)
        self.bind_addr = socket_addr

    def accept(self):
        data, addr = self.get_data("SYN")
        while not isinstance(data, SYN):
            data, addr = self.get_data("SYN")
            print(
                f"Waitng for client's SYN packet, please make sure that client is connected to {self.bind_addr}"
            )
        for i in range(self.factor):
            self.sock.sendto(SYNACK(self.rwnd, data).serialize(), addr)
            sleep(1 / self.factor)
        print(f"ESTABLISHED Client {addr=},  window size = {data.rwnd}")
        self.peer = addr
        self.state = ServerState.ESTABLISHED
        self.sender = Thread(target=self.sender_func, args=(data.rwnd,))
        self.sender.start()
        self.receiver.start()

    def send(self, stream_id: int, data: bytes):
        super().send(stream_id, data)

    def recv(self) -> tuple[int, bytes]:
        return super().recv()

    def close(self):
        super().close()
