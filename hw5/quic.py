import socket
import pickle


class QUIC:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(1)
        self.verbose = True

    def get_data(self, msg) -> tuple:
        while True:
            try:
                raw, addr = self.sock.recvfrom(1024)
                data = pickle.loads(raw)
                if self.verbose:
                    print(data, addr)
            except TimeoutError as e:
                if self.verbose:
                    print(msg, e)
                return (None, None)
            else:
                return (data, addr)
