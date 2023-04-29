import socket
import pickle
from packet import Stream, SYN, SYNACK, Packet, ACK, FIN
from threading import Thread, Lock, Event
from time import sleep
from queue import Queue
from copy import deepcopy
import time
import heapq


class QUIC:
    def __init__(self) -> None:
        self.verbose = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(1)
        self.factor = 10
        self.rwnd = 100000
        self.sender: Thread
        self.receiver = Thread(target=self.__receiver_func)
        self.olock = Lock()
        self.ostream: dict[int, Queue] = dict()

        self.ostreams: dict[int, int] = dict()

        self.peer: tuple[str, int]

        self.plock = Lock()
        self.pkts: dict[int, Packet] = dict()

        self.seq = 0
        self.ack = 0

        self.base = -1

        self.ilock = Lock()
        self.istream: dict[int, Queue[tuple[int, bytes]]] = dict()
        self.istreams: dict[int, int] = dict()

        self.stop = Event()
        self.stopr = Event()

    def sender_func(self, sz=100):
        while True:
            cnt = 0
            with self.plock:
                for seq, pkt in self.pkts.items():
                    if cnt >= sz:
                        continue
                    if self.base <= seq and time.time() - pkt.lsend > 0.1:
                        pkt.ack = self.ack
                        if self.verbose:
                            print("send:", pkt)
                        pkt.lsend = time.time()
                        cnt += 1
                        self.sock.sendto(pkt.serialize(), self.peer)
                        # sleep(1)
                    else:
                        # print(f"{seq=} acked")
                        pass
                if self.verbose:
                    print(self.base, len(self.pkts), end=" => ")
                self.pkts = {k: v for k, v in self.pkts.items() if k >= self.base}
                if self.verbose:
                    print(len(self.pkts))
                if self.stop.is_set() and len(self.pkts) == 0:
                    if self.verbose:
                        print("sender stop")
                    return
            sleep(0.1)
        pass

    def __receiver_func(self):
        while True:
            pkt = self.get_data()[0]
            while pkt.ack == -1:
                pkt = self.get_data()[0]
                if self.stopr.is_set():
                    if self.verbose:
                        print("receiver stop")
                    return
            # print("recv:", pkt)
            if isinstance(pkt, ACK):
                assert pkt.seq == -1, "Invalid ack"
                self.base = max(self.base, pkt.ack)
            else:
                if pkt.seq == self.ack:
                    self.ack += 1
                ack = ACK(-1, self.ack, pkt.seq)
                # print(f"send ack {ack}")
                self.sock.sendto(ack.serialize(), self.peer)
                self.add_stream(pkt)
            # sleep(1)
        pass

    def add_stream(self, pkt: Packet):
        with self.ilock:
            if pkt.sid not in self.istream:
                self.istream[pkt.sid] = Queue()
                self.istreams[pkt.sid] = 0
            q = self.istream[pkt.sid]
        q.put((pkt.offset, pkt.data))

    def get_data(self, msg="") -> tuple[Packet, tuple[str, int]]:
        try:
            raw, addr = self.sock.recvfrom(1024)
            self.addr = addr
            data = pickle.loads(raw)
            if self.verbose:
                # print(data, addr)
                pass
        except TimeoutError as e:
            if self.verbose and msg != "SYN":
                # print(e, msg)
                pass
            return (Packet(-1), ("", -1))
        else:
            return (data, addr)

    def send(self, stream_id: int, data: bytes):
        if stream_id not in self.ostreams:
            self.ostreams[stream_id] = 0

        while len(data) > 0:
            pkt = Packet(self.seq)
            self.seq += 1
            pkt.sid = stream_id
            pkt.offset = self.ostreams[stream_id]
            if len(data) < 800:
                pkt.data = data
                self.ostreams[stream_id] += len(data)
                data = b""
            else:
                pkt.data = data[:800]
                self.ostreams[stream_id] += 800
                data = data[800:]
            with self.plock:
                self.pkts[pkt.seq] = pkt
        if self.verbose:
            print(f"sent {stream_id}")

    def recv(self) -> tuple[int, bytes]:
        while True:
            with self.ilock:
                for k, v in self.istream.items():
                    if v.qsize():
                        fst = v.get()
                        v.put(fst)
                        while True:
                            front = v.get()
                            if self.istreams[k] == front[0]:
                                self.istreams[k] += len(front[1])
                                return k, front[1]
                            v.put(front)
                            if front == fst:
                                # print(f"No matched in stream {k}")
                                break
            if self.verbose:
                print("recv waiting")
            sleep(0.05)
        return (0, b"abc123")

    def close(self):
        self.stop.set()
        self.sender.join()
        print("closing...")
        sleep(5)
        self.stopr.set()
        self.receiver.join()
