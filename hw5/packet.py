import pickle
from queue import Queue


class Packet:
    def __init__(self, seq: int) -> None:
        self.seq: int = seq
        self.ack: int = -1

        self.data: bytes = b""
        self.sid: int = -1
        self.offset: int = -1

        self.lsend: float = 0

        self.rwnd: int

    def __len__(self):
        return len(self.data)

    def __repr__(self) -> str:
        return f"seq={self.seq} ack={self.ack} sid={self.sid} off={self.offset} len={len(self.data)}"

    def serialize(self) -> bytes:
        return pickle.dumps(self)


class SYN(Packet):
    def __init__(self, rwnd: int) -> None:
        super().__init__(0)
        self.rwnd: int = rwnd


class SYNACK(Packet):
    def __init__(self, rwnd: int, syn: Packet) -> None:
        assert isinstance(syn, SYN)
        if syn == None:
            assert False
        super().__init__(0)
        self.rwnd = rwnd


class ACK(Packet):
    def __init__(self, seq: int, cack: int, pack: int) -> None:
        super().__init__(0)
        self.seq = seq
        self.ack = cack
        self.pack = pack


class FIN(Packet):
    def __init__(self) -> None:
        super().__init__(0)


class Stream:
    def __init__(self, id: int) -> None:
        self.id: int = id
        self.buf: Queue[tuple[int, bytes]] = Queue()
