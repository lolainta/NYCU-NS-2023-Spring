from quic import QUIC
from packet import Packet, SYN, SYNACK
import pickle
from states import ServerState


class QUICServer(QUIC):
    def __init__(self) -> None:
        super().__init__()
        self.state = ServerState.IDLE
        self.client = None
        self.verbose = True
        self.seq = 0

    def listen(self, socket_addr: tuple[str, int]):
        """this method is to open the socket"""
        self.sock.bind(socket_addr)
        pass

    def accept(self):
        """this method is to indicate that the client
        can connect to the server now"""
        while True:
            match self.state:
                case ServerState.IDLE:
                    data, addr = self.get_data("SYN")
                    while data is None:
                        data, addr = self.get_data("SYN")

                    if not isinstance(data, SYN):
                        print(f"ERROR: SYN expected, got {data}")
                    self.client = addr
                    pkt = SYNACK(self.seq, data)
                    self.sock.sendto(pkt.serialize(), self.client)
                    self.state = ServerState.SYN_RCVD

                case ServerState.SYN_RCVD:
                    data, addr = self.get_data(self.state)
                    if data is None:
                        self.state = ServerState.IDLE
                        self.client = None
                    else:
                        if not isinstance(data, SYNACK):
                            print(f"ERROR: {data} is not an SYNACK packet")
                        if not addr == self.client:
                            print(f"ERROR: SYNACK addr differ, {addr} != {self.client}")
                        self.state = ServerState.ESTABLISHED
                        print(f"ESTABLISHED with {self.client=}")
                        return
                case _:
                    assert False, "Unknown State"
        pass

    def send(self, stream_id: int, data: bytes):
        """call this method to send data, with non-reputation stream_id"""
        pass

    def recv(self) -> tuple[int, bytes]:  # stream_id, data
        """receive a stream, with stream_id"""
        self.sock.recvfrom(1024)
        return (1, b"abc123")

    def close(self):
        """close the connection and the socket"""
        pass
