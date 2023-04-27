import pickle


class Packet:
    def __init__(self, seq: int, ack: int, data) -> None:
        self.seq = seq
        self.ack = ack
        self.data = data

    def __len__(self):
        return len(self.data)

    def __repr__(self) -> str:
        return f"{self.seq} {self.ack} {self.data}"

    def serialize(self) -> bytes:
        return pickle.dumps(self)


class SYN(Packet):
    def __init__(self, seq: int, ack: int) -> None:
        super().__init__(seq, ack, "SYN")


class SYNACK(Packet):
    def __init__(self, seq: int, syn: SYN) -> None:
        if syn == None:
            assert False
        super().__init__(seq, syn.seq + len(syn), "SYNACK")
