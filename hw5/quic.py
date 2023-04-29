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
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.settimeout(1)
        self.ilock = Lock()
        self.olock = Lock()
        self.qlock = Lock()
        self.verbose = False
        self.ostream: dict[tuple[int, tuple[str, int]], Stream] = dict()
        self.istream: dict[tuple[int, tuple[str, int]], Stream] = dict()
        self.rwnd = 10000
        self.sender = Thread(target=self.__sender_func)
        self.receiver = Thread(target=self.__receiver_func)
        self.seq = 0
        self.ack = 0
        self.event = Event()
        self.got_fin = False
        self.factor = 100
        self.got = list()
        self.obuf: Queue[tuple[tuple[str, int], Packet, float]] = Queue(1000)
        # self.need_ack: dict[int, tuple[tuple[str, int], int, int, bytes]] = dict()
        self.receiv_data: dict[tuple[int, tuple[str, int]], bytes] = dict()

    def __round(self):
        if not self.obuf.empty():
            if self.verbose:
                print("round sending", self.obuf.qsize())
            with self.qlock:
                addr, pre, tmp = self.obuf.get()
                self.obuf.put((addr, pre, tmp))
            # self.sock.sendto(pre.serialize(), addr)
            while True:
                with self.qlock:
                    addr, cur, tmp = self.obuf.get()
                    if time.time() - tmp > self.obuf.qsize() * 0.01:
                        # if self.verbose:
                        print(f"resend {cur}")
                        self.sock.sendto(cur.serialize(), addr)
                        self.obuf.put((addr, cur, time.time()))
                    else:
                        self.obuf.put((addr, cur, tmp))
                if cur == pre:
                    break
            # print("round sended")
            sleep(self.obuf.qsize() * 0.1)

    def __rm(self, lb: int, ub: int):
        if not self.obuf.empty():
            with self.qlock:
                fst = self.obuf.get()
                self.obuf.put(fst)
            while True:
                with self.qlock:
                    ele = self.obuf.get()
                    if self.verbose:
                        # print(f"{ele[1]} {lb} {ub}")
                        pass
                    if lb <= ele[1].seq and ele[1].seq < ub:
                        if self.verbose:
                            print(f"Got ACK remove {ele[1]} from obuf")
                            pass
                    else:
                        self.obuf.put(ele)
                    if ele == fst:
                        break

    def __sender_func(self):
        while True:
            if self.event.is_set():
                break
            self.__round()
            with self.olock:
                for key in self.ostream.keys():
                    sid, addr = key
                    if self.ostream[key].buf.qsize() > 0:
                        # print("sender")
                        # print(self.ostream)
                        off, data = self.ostream[key].buf.get()
                        pkt = Packet(self.seq, self.ack, data)
                        pkt.stream = sid
                        pkt.offset = off
                        # print(f"{off=}")
                        # pkt.rwnd = -1
                        self.obuf.put((addr, pkt, time.time()))
                        self.seq += 1
                        self.sock.sendto(pkt.serialize(), addr)
                        if self.verbose:
                            print("sender send", pkt)
            sleep(0.1)

    def __lack(self, new: int) -> int:
        if new >= self.ack:
            heapq.heappush(self.got, new)
        if len(self.got) == 0:
            if self.verbose:
                print("heap empty")
            return self.ack
        top = heapq.heappop(self.got)
        while len(self.got) and top < self.ack:
            top = heapq.heappop(self.got)
        if top == self.ack:
            self.ack += 1
            if self.verbose:
                print(f"current ack = {self.ack}")
        else:
            heapq.heappush(self.got, top)
        return self.ack

    def __receiver_func(self):
        while True:
            # if self.event.is_set():
            #     break
            data, addr = self.get_data("receiver_func")
            if data.data is None or isinstance(data, SYN) or isinstance(data, SYNACK):
                if self.got_fin:
                    if self.verbose:
                        print("got fin receiver break")
                    break
                else:
                    if self.verbose:
                        print("not got fin yet")
                        pass
            else:
                with self.ilock:
                    assert isinstance(data, Packet)
                    if (data.stream, addr) not in self.istream:
                        self.istream[(data.stream, addr)] = Stream(data.stream)
                    if isinstance(data, ACK):
                        if self.verbose:
                            print(f"GOT ACK {data.ack} {data.ub}")
                        self.__rm(data.ack, data.ack + 1)
                        self.__rm(0, data.ub)
                    elif isinstance(data, FIN):
                        print("GOT FIN")
                        self.got_fin = True
                        break
                    else:
                        if data.seq < self.ack:
                            continue
                        print(f"receiver receive {data}")

                        pkt = ACK(data.seq)
                        pkt.ub = self.__lack(data.seq)
                        print(pkt.ub)
                        self.sock.sendto(pkt.serialize(), addr)
                        if self.istream[(data.stream, addr)].ub > data.offset:
                            continue
                        print(data, self.ack)
                        if self.verbose:
                            print("put", data)
                        self.istream[(data.stream, addr)].buf.put(
                            (data.offset, data.data)
                        )
                        # print(self.istream)
                        # for i in range(10):
                        if self.verbose:
                            print(f"send ack {pkt}")
                        self.sock.sendto(pkt.serialize(), addr)
            # sleep(0.01)

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
                print(e, msg)
            return (Packet(0, 0, None), ("", 0))
        else:
            return (data, addr)

    def send(self, stream_id: int, data: bytes, addr: tuple[str, int]):
        # print("send aquire")
        with self.olock:
            if (stream_id, addr) not in self.ostream:
                self.ostream[(stream_id, addr)] = Stream(stream_id)
            idx = self.ostream[(stream_id, addr)].ub
            while len(data) > 0:
                if len(data) <= 800:
                    self.ostream[(stream_id, addr)].buf.put((idx, data))
                    idx += 1
                    break
                else:
                    self.ostream[(stream_id, addr)].buf.put((idx, data[:800]))
                    data = data[800:]
                    idx += 1
            self.ostream[(stream_id, addr)].ub = idx
        # print(self.ostream)
        # print("send release")

    def recv(self) -> tuple[int, bytes]:
        while True:
            # print("recv aquire")
            with self.ilock:
                # print(self.istream)
                for key in self.istream.keys():
                    if self.istream[key].buf.qsize() > 0:
                        off, data = self.istream[key].buf.get()
                        # print(off, data)
                        if off < self.istream[key].lb:
                            continue
                        elif off == self.istream[key].lb:
                            self.istream[key].lb += 1
                            # print("return")
                            return key[0], data
                        else:
                            self.istream[key].buf.put((off, data))
            # print("recv release")
            sleep(0.1)

    def close(self):
        sleep(1)
        while True:
            if self.obuf.empty():
                with self.olock:
                    if all([v.buf.empty() for k, v in self.ostream.items()]):
                        self.event.set()
                        break
            # sleep(0.1)
        print("osream empty")
        t = time.time()
        while self.got_fin == False:
            # print("send fin")
            self.sock.sendto(FIN().serialize(), self.addr)
            # sleep(0.1)
            if time.time() - t > 5:
                self.got_fin = True
                break
        self.sender.join()
        self.receiver.join()
