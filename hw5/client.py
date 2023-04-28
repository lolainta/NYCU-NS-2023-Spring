from quic_client import QUICClient


def main():
    client = QUICClient()
    client.connect(("localhost", 30000))
    recv_id, recv_data = client.recv()
    print(recv_data.decode("utf-8"))
    client.send(recv_id, b"Hello Server!")
    client.close()


if __name__ == "__main__":
    main()
