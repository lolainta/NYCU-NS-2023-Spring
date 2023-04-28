from quic_server import QUICServer


def main():
    server = QUICServer()
    server.listen(("", 30000))
    server.accept()
    server.send(1, b"SOME DATA, MAY EXCEED 1500 bytes")
    recv_id, recv_data = server.recv()
    print(recv_data.decode("utf-8"))

    server.close()


if __name__ == "__main__":
    main()
