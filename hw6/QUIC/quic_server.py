from .common.packet import Packet, Frame
from .common.helper import Buffer
import socket
import threading
import math, time
from copy import deepcopy

now = lambda: time.time()

class QUICServer:
    def __init__(self) -> None:
        self.client_addr = None

        # quic
        self.send_wait_list = []
        self.sender_window = Buffer(size=4)
        self.ssthresh = 32
        self.no_resend_list = []
        self.recv_window = {}
        self.recv_window_limit = 16
        self.recv_stream_length = {}
        self.recv_stream_offsets = {}
        self.recv_read_ptr = {}
        self.send_offsets = {}
        self.finished_stream = []
        self.pkt_num = 1
        self.slow_start = True

        # threading
        self.is_running = True
        self.send_manager = threading.Thread(target=self.send_task)
        self.receive_manager = threading.Thread(target=self.recv_task)
        self.meter_manager = threading.Thread(target=self.meter_task)

        # meter
        self.byte_counter = 0

    def listen(self, sockaddr):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(sockaddr)

    def accept(self):
        # expect client init packet
        data, sockaddr = self.sock.recvfrom(1500)
        pkt = Packet()
        pkt.deserialize(data)
        # check if is init packet
        assert pkt.header.header_form == 1
        assert pkt.header.packet_type == 0x00
        if pkt.frame.type == Frame.MAX_DATA:
            self.sender_window.size = pkt.frame.max_data
        # set client addr
        self.client_addr = sockaddr

        # send back init packet
        pkt = Packet()
        pkt.header.header_form = 1
        pkt.header.packet_type = 0x00
        pkt.header.dst_id = 0
        pkt.header.src_id = 0
        pkt.header.length = 5
        pkt.header.pkt_num = self.pkt_num_inc()
        pkt.header.payload_len = 1
        pkt.frame.type = Frame.MAX_DATA
        pkt.frame.max_data = self.recv_window_limit
        dat = pkt.serialize()

        self.sock.sendto(dat, sockaddr)

        # create thread
        self.send_manager.daemon = True
        self.receive_manager.daemon = True
        self.meter_manager.daemon = True
        self.send_manager.start()
        self.receive_manager.start()
        # self.meter_manager.start()


    def send(self, stream_id, data, end=False):
        pkt = Packet()

        if type(stream_id) == list and type(data) == list:
            stream_id_data = {}
            for i, id in enumerate(stream_id):
                ptr = 0
                stream_id_data[id] = []
                while ptr <= len(data[i]):
                    stream_id_data[id].append((ptr, data[i][ptr:min(ptr+1400, len(data[i]))]))
                    ptr += 1400

            while all([len(datas) != 0 for datas in stream_id_data.values()]):
                for id, datas in stream_id_data.items():
                    if len(datas) != 0:
                        offset, data = datas.pop(0)
                        pkt.clear()
                        pkt.header.header_form = 0
                        pkt.header.pkt_num = self.pkt_num_inc()
                        pkt.header.dst_id = 0
                        pkt.frame.type = Frame.STREAM if len(datas) != 0 else Frame.STREAM | Frame.FIN
                        pkt.frame.stream_id = id
                        pkt.frame.offset = offset
                        pkt.frame.stream_data = data
                        pkt.frame.length = len(pkt.frame.stream_data)
                        b = pkt.serialize()
                        self.send_wait_list.append((pkt.header.pkt_num, b, 0.0))

                    
        elif type(stream_id) == int and type(data) == bytes:
            if stream_id not in self.send_offsets.keys():
                self.send_offsets[stream_id] = 0
            i = 0
            while i <= len(data):
                pkt.clear()
                pkt.header.header_form = 0
                pkt.header.pkt_num = self.pkt_num_inc()
                pkt.header.dst_id = 0
                if end:
                    pkt.frame.type = Frame.STREAM if i + 1400 < len(data) else Frame.STREAM | Frame.FIN
                else:
                    pkt.frame.type = Frame.STREAM
                pkt.frame.stream_id = stream_id
                pkt.frame.offset = i + self.send_offsets[stream_id]
                pkt.frame.stream_data = data[i:min(i+1400, len(data))]
                pkt.frame.length = len(pkt.frame.stream_data)
                b = pkt.serialize()
                self.send_wait_list.append((pkt.header.pkt_num, b, 0.0))

                
                i += 1400
                
            self.send_offsets[stream_id] += i

    def send_task(self):
        while self.is_running:
            # move queue packet to sender window to send
            while not self.sender_window.is_full() and len(self.send_wait_list) != 0:
                self.sender_window.get_buf().append(self.send_wait_list.pop(0))

            halve = False
            for i, (pkt_num, b, t) in enumerate(self.sender_window.get_buf()):
                if t == 0.0 or now() - t > 1.0:
                    if now() - t > 1.0:
                        halve = True
                    self.sender_window.get_buf()[i] = (pkt_num, b, now())
                    self.sock.sendto(b, self.client_addr)

            if halve:
                self.sender_window.halve_size()
                self.slow_start = False

            while len(self.no_resend_list) != 0:
                self.sock.sendto(self.no_resend_list.pop(0), self.client_addr)

    def recv_task(self):
        pkt = Packet()
        reply = Packet()
        while self.is_running:
            try:
                b, addr = self.sock.recvfrom(1500)
            except:
                self.close()
            self.byte_counter += len(b)
            pkt.deserialize(b)
            assert pkt.header.header_form == 0
            if pkt.frame.type == Frame.ACK:
                pkt_num_to_del = pkt.frame.first_ack_range
                for i, (pkt_num, _, _) in enumerate(self.sender_window.get_buf()):
                    if pkt_num == pkt_num_to_del:
                        del self.sender_window.get_buf()[i]
                
                # congestion control
                if self.slow_start:
                    self.sender_window.double_size()
                else:
                    self.sender_window.add_size()
                if self.sender_window.get_size() >= self.ssthresh:
                    self.slow_start = False

            elif pkt.frame.type == Frame.STREAM or pkt.frame.type == Frame.STREAM | Frame.FIN:
                id = pkt.frame.stream_id
                # new stream
                if id not in self.recv_window:
                    self.recv_window[id] = []
                    self.recv_stream_offsets[id] = []
                    self.recv_read_ptr[id] = 0
                
                now_pos = math.ceil(pkt.frame.offset / 1400)

                # bypass same packet
                if pkt.frame.offset in self.recv_stream_offsets.get(id):
                    reply.clear()
                    reply.header.header_form = 0
                    reply.header.pkt_num = self.pkt_num_inc()
                    reply.frame.type = Frame.ACK
                    reply.frame.largest_ack = pkt.header.pkt_num
                    reply.frame.first_ack_range = pkt.header.pkt_num
                    b = reply.serialize()
                    self.no_resend_list.append(b)
                    continue
                else:
                    self.recv_stream_offsets[id].append(pkt.frame.offset)
                
                # reordering
                if len(self.recv_window[id]) == now_pos:
                    # ordered
                    self.recv_window[id].append(pkt.frame.stream_data)
                elif len(self.recv_window[id]) < now_pos:
                    # laters arrived earlier
                    left = now_pos - len(self.recv_window[id])
                    for i in range(left):
                        self.recv_window[id].append(None)
                    self.recv_window[id].append(pkt.frame.stream_data)
                else:
                    # earlies arrived later
                    self.recv_window[id][now_pos] = pkt.frame.stream_data

                # the last frame
                if pkt.frame.type == Frame.STREAM | Frame.FIN:
                    self.recv_stream_length[id] = now_pos + 1
                
                # check frame finish
                for id, pieces in self.recv_stream_length.items():
                    if len(self.recv_window[id]) == pieces and \
                            id not in self.finished_stream and \
                            None not in self.recv_window[id]:
                        self.finished_stream.append(id)

                # reply ACK
                reply.clear()
                reply.header.header_form = 0
                reply.header.pkt_num = self.pkt_num_inc()
                reply.frame.type = Frame.ACK
                reply.frame.largest_ack = pkt.header.pkt_num
                reply.frame.first_ack_range = pkt.header.pkt_num
                b = reply.serialize()
                self.no_resend_list.append(b)

    def meter_task(self):
        while self.is_running:
            self.byte_counter = 0
            time.sleep(1)

    def recv(self):
        # if not self.is_running:
        #     return None, None
        # while len(self.finished_stream) == 0:
        #     pass
        # stream_id = self.finished_stream.pop(0)
        # del self.recv_stream_length[stream_id]
        # data = b''.join(self.recv_window.pop(stream_id))
        # return stream_id, data

        # print(self.recv_window)
        while self.is_running:
            keys = list(self.recv_window.keys())
            for k in keys:
                try:
                    part = self.recv_window[k][self.recv_read_ptr[k]]
                    if part:
                        if self.recv_read_ptr[k] == len(self.recv_window[k]) - 1  and \
                        k in self.finished_stream:
                            del self.recv_stream_length[k]
                            del self.recv_window[k]
                            return k, part, True
                        else:
                            self.recv_read_ptr[k] += 1
                            return k, part, False
                except:
                    pass
        return None, None, False

    def close(self):
        self.is_running = False
        self.send_wait_list.clear()
        self.sender_window._buf.clear()
        self.sender_window.size = 4
        self.no_resend_list.clear()
        self.recv_window.clear()
        self.recv_stream_length.clear()
        self.recv_stream_offsets.clear()
        self.finished_stream.clear()
        self.sock.close()
    
    def pkt_num_inc(self):
        r = self.pkt_num
        self.pkt_num += 1
        return r

if __name__ == "__main__":
    server = QUICServer()
    server.listen(("", 30000))
    server.accept()
    data = "1" * 1000 * 5
    server.send(1, data.encode("utf-8"))
    print("send 1")
    data = "2" * 1000 * 5
    server.send(1, data.encode("utf-8"), True)
    print("send 2")
    while True:
        pass
