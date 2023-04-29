from quic_server import QUICServer
import random
import string

DATA_LEN = int(1e4)


def main():
    server = QUICServer()
    server.verbose = False
    server.listen(("", 30000))
    server.accept()
    server.send(100, b"SOME DATA, MAY EXCEED 1500 bytes")
    recv_id, recv_data = server.recv()
    print(recv_data.decode("utf-8"))
    random.seed(45510)
    data: dict[int, str] = dict()
    for i in range(5):
        data[i] = "".join(random.choices(string.ascii_letters, k=DATA_LEN))

    for k, v in data.items():
        server.send(k, bytes(v.encode()))

    server.close()


if __name__ == "__main__":
    main()
