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
        self.verbose = 2
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(1)
        self.factor = 100
        self.rwnd = 100000

        self.sender: Thread
        self.receiver = Thread(target=self.__receiver_func)

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

        self.stops = Event()
        self.stopr = Event()

        self.resend_cnt = 0

        self.got = list()

    def sender_func(self, sz=100):
        while True:
            cnt = 0
            if self.verbose >= 3:
                print(f"{self.resend_cnt=}")
            self.resend_cnt = 0
            with self.plock:
                for seq, pkt in self.pkts.items():
                    if cnt >= sz:
                        continue
                    if self.base <= seq and time.time() - pkt.lsend > 0.01:
                        if pkt.lsend > 0:
                            self.resend_cnt += 1
                            # print("resend count = ", self.resend_cnt)
                        pkt.ack = self.ack
                        if self.verbose >= 2:
                            print("send:", pkt)
                        pkt.lsend = time.time()
                        cnt += 1
                        self.sock.sendto(pkt.serialize(), self.peer)
                        # sleep(0.001)
                    else:
                        if self.verbose >= 2:
                            print(f"{seq=} acked")
                if self.verbose >= 1:
                    print(self.base, len(self.pkts), end=" => ")
                self.pkts = {k: v for k, v in self.pkts.items() if k >= self.base}
                if self.verbose >= 1:
                    print(len(self.pkts))
                if self.stops.is_set() and len(self.pkts) == 0:
                    if self.verbose >= 1:
                        print("sender stop")
                    return
            sleep(0.01)
        pass

    def flush_acked(self):
        pass

    def __receiver_func(self):
        while True:
            pkt = self.get_data()[0]
            while pkt.ack == -1:
                pkt = self.get_data()[0]
                if self.stopr.is_set():
                    if self.verbose >= 1:
                        print("receiver stop")
                    return
            # print("recv:", pkt)
            if isinstance(pkt, ACK):
                assert pkt.seq == -1, "Invalid ack"
                if pkt.pack >= self.base:
                    with self.plock:
                        if pkt.pack in self.pkts:
                            del self.pkts[pkt.pack]
                self.base = max(self.base, pkt.ack)
            else:
                # if pkt.sid == 3:
                #     continue
                self.mex(pkt.seq)
                # if pkt.seq == self.ack:
                #     self.ack += 1
                ack = ACK(-1, self.ack, pkt.seq)
                if self.verbose >= 2:
                    print(f"send ack {ack}")
                self.sock.sendto(ack.serialize(), self.peer)
                self.add_stream(pkt)

    def mex(self, new: int):
        if new < self.ack:
            return
        heapq.heappush(self.got, new)
        if new > self.ack:
            return
        top = heapq.heappop(self.got)
        while top <= self.ack:
            if top == self.ack:
                self.ack += 1
            else:
                if len(self.got):
                    top = heapq.heappop(self.got)
                else:
                    break
        heapq.heappush(self.got, top)
        return

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
            if self.verbose >= 3:
                print(data, addr)
        except TimeoutError as e:
            if self.verbose >= 3:
                print(e, msg)
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
        if self.verbose >= 1:
            print(f"sent {stream_id}")

    def recv(self) -> tuple[int, bytes]:
        while True:
            wtime = 0
            with self.ilock:
                for k, v in self.istream.items():
                    wtime += v.qsize()
                    if v.qsize():
                        fst = v.get()
                        v.put(fst)
                        while True:
                            front = v.get()
                            if self.istreams[k] == front[0]:
                                self.istreams[k] += len(front[1])
                                return k, front[1]
                            if front[0] > self.istreams[k]:
                                v.put(front)
                            if front == fst:
                                if self.verbose >= 2:
                                    print(f"No matched in stream {k}")
                                break
            if self.verbose >= 1:
                print("recv waiting")
            # print(f"receiver: {wtime=}")
            sleep(0.001)
            # sleep(1 / (wtime + 10))

    def close(self):
        self.stops.set()
        self.sender.join()
        print("closing...")
        sleep(3)
        self.stopr.set()
        self.receiver.join()
