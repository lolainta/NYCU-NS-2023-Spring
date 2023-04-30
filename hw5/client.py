from quic_client import QUICClient
import random
import string
import time
from config import STREAM_NUM, DATA_LEN


def main():
    client = QUICClient()
    client.verbose = 0
    client.connect(("localhost", 30000))
    recv_id, recv_data = client.recv()
    print(recv_data.decode("utf-8"))
    client.send(recv_id, b"Hello Server!")

    res = dict()
    strart = time.time()
    loaded = 0
    while True:
        recv_id, recv_data = client.recv()
        loaded += len(recv_data)

        # Record Data
        if recv_id not in res:
            res[recv_id] = b""
        res[recv_id] += recv_data
        """
        # Print Status
        print()
        for k, v in res.items():
            print(f"{k}: {len(v)}", end=", ")
        print()
        """
        # Print Speed
        cur = time.time()
        print(
            f"average speed = {loaded*8/1000/(cur-strart):.3f} Kbps: {loaded} bytes in {cur-strart:.3f} seconds",
            end="\r",
        )

        if all([len(v) == DATA_LEN for v in res.values()]) and len(res) == 5:
            print("done")
            break

    client.close()

    # Verify Data
    random.seed(45510)
    data = dict()
    for i in range(STREAM_NUM):
        data[i] = "".join(random.choices(string.ascii_letters, k=DATA_LEN))

    print(res.keys(), data.keys())

    for k in range(STREAM_NUM):
        assert bytes(data[k].encode()) == res[k], (data[k], res[k])
    print("Data verified")


if __name__ == "__main__":
    main()
