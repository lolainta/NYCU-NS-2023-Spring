import pickle
from queue import Queue


class Packet:
    def __init__(self, seq: int, ack: int, data) -> None:
        self.seq = seq
        self.ack = ack

        self.data = data
        self.stream = -1
        self.offset = -1
        self.rwnd = -1

    def __len__(self):
        return len(self.data)

    def __repr__(self) -> str:
        return f"{self.stream} {self.offset} {self.data}"

    def serialize(self) -> bytes:
        return pickle.dumps(self)


class SYN(Packet):
    def __init__(self, rwnd: int) -> None:
        super().__init__(0, 0, "SYN")
        self.rwnd: int = rwnd


class SYNACK(Packet):
    def __init__(self, rwnd: int, syn: SYN) -> None:
        if syn == None:
            assert False
        super().__init__(0, 0, "SYNACK")
        self.rwnd: int = rwnd


class ACK(Packet):
    def __init__(self, ack: int) -> None:
        super().__init__(0, ack, "ACK")


class FIN(Packet):
    def __init__(self) -> None:
        super().__init__(0, 0, "FIN")


class Stream:
    def __init__(self, id: int) -> None:
        self.id: int = id
        self.buf: Queue[tuple[int, bytes]] = Queue()
        self.ub: int = 0
        self.lb: int = 0
