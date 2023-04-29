from RDTClient import RDTClient
import random
import string
import time

DATA_LEN = int(1e6)


def main():
    client = RDTClient()
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
        for k, v in res.items():
            print(f"{k}: {len(v)}", end=", ")
        print()
        cur = time.time()
        print(
            f"average speed={loaded*8/1000/(cur-strart):.3f} Kbps: {loaded} bytes in {cur-strart:.3f} seconds",
            end="\n",
        )
        """
        if all([len(v) == DATA_LEN for v in res.values()]) and len(res) == 5:
            print("done")
            break
    client.close()

    # Print Status
    cur = time.time()
    print(
        f"average speed={loaded*8/1000/(cur-strart):.3f} Kbps: {loaded} bytes in {cur-strart:.3f} seconds",
        end="\n",
    )

    # Verify Data
    random.seed(45510)
    data = dict()
    for i in range(5):
        data[i] = "".join(random.choices(string.ascii_letters, k=DATA_LEN))

    print(res.keys(), data.keys())

    for k in range(5):
        assert bytes(data[k].encode()) == res[k], (data[k], res[k])
    print("Data verified")


if __name__ == "__main__":
    main()
