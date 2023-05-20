import socket
import threading
import time
from Utils import Frame
from Utils import Parser

import os
import glob
import threading
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from collections import deque


class Response:
    def __init__(self, stream_id, headers={}, status="Not yet") -> None:
        self.stream_id = stream_id
        self.headers = headers

        self.status = status
        self.body = b""

        self.contents = deque()
        self.complete = False

    def get_headers(self):
        begin_time = time.time()
        while self.status == "Not yet":
            if time.time() - begin_time > 5:
                return None
        return self.headers

    def get_full_body(self):  # used for handling short body
        begin_time = time.time()
        while not self.complete:
            if time.time() - begin_time > 5:
                return None
        if len(self.body) > 0:
            return self.body
        while len(self.contents) > 0:
            self.body += self.contents.popleft()
        return self.body  # the full content of HTTP response body

    def get_stream_content(self):  # used for handling long body
        begin_time = time.time()
        while (
            len(self.contents) == 0
        ):  # contents is a buffer, busy waiting for new content
            if (
                self.complete or time.time() - begin_time > 5
            ):  # if response is complete or timeout
                return None
        content = self.contents.popleft()  # pop content from deque
        return content  # the part content of the HTTP response body


class HTTPClient:
    def __init__(self) -> None:
        self.connecting = False

    def __get_next_stream_id(self):
        stream_id = self.next_stream_id
        self.next_stream_id += 2
        return stream_id

    def connect(self, host="127.0.0.1", port=8080):
        if not self.connecting:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            try:
                self.socket.connect((host, port))

                self.connecting = True
                self.recv_buffer = b""
                self.recv_streams = {}
                self.send_buffers = {}
                self.next_stream_id = 1
                self.recv_thread = threading.Thread(target=self.__recv_loop)
                self.recv_thread.start()
                self.send_thread = threading.Thread(target=self.__send_loop)
                self.send_thread.start()
            except Exception as e:
                print(e)
                self.connecting = False
                self.socket.close()

    def __complete_stream(self, stream_id):
        if stream_id in self.recv_streams:
            self.recv_streams[stream_id]["complete"] = True

    def wait_for_response(self, stream_id):
        response = {
            "version": "HTTP/2.0",  # e.g. "HTTP/1.0"
            "status": "",  # e.g. "200 OK"
            "headers": {},  # e.g. {content-type: application/json}
            "body": "",  # e.g. "{'id': params['id'], 'key': hmac_sha256(params['id'], 'http10')}"
        }
        wait_count = 0
        while self.connecting:
            if wait_count > 300:
                return None
            if stream_id not in self.recv_streams:
                return None
            if (
                "complete" in self.recv_streams[stream_id]
                and self.recv_streams[stream_id]["complete"]
            ):
                try:
                    response["headers"] = self.recv_streams[stream_id]["headers"]
                    response["body"] = self.recv_streams[stream_id]["body"].decode(
                        "utf-8"
                    )
                    response["status"] = response["headers"][":status"]
                except:
                    return None
                del self.recv_streams[stream_id]
                ret = Response(stream_id, response["headers"], response["status"])
                ret.contents.append(response["body"].encode())
                ret.complete = True
                return ret
            wait_count += 1
            time.sleep(0.01)
        del self.recv_streams[stream_id]
        return None

    def __send_loop(self):
        while self.connecting:
            try:
                end_streams = []
                keys = list(self.send_buffers.keys())
                for key in keys:
                    if len(self.send_buffers[key]) > 0:
                        frame = self.send_buffers[key].pop(0)
                        self.socket.sendall(frame.to_bytes())
                        if frame.flags == 1:
                            end_streams.append(key)
                        time.sleep(0.002)
                for key in end_streams:
                    del self.send_buffers[key]
            except Exception as e:
                print(e)
                self.connecting = False
                self.socket.close()
                break

    def __recv_loop(self):
        while self.connecting:
            try:
                recv_bytes = self.socket.recv(4096)
                if not recv_bytes:
                    self.connecting = False
                    self.socket.close()
                    break
                recv_bytes = self.recv_buffer + recv_bytes
                # parse request
                frames, remain_bytes = Frame.bytes_to_frames(recv_bytes)
                self.recv_buffer = remain_bytes
                for frame in frames:
                    if frame.type == 0:  # data
                        self.recv_streams[frame.stream_id]["body"] += frame.payload
                    elif frame.type == 1:  # header
                        if frame.stream_id not in self.recv_streams:
                            self.recv_streams[frame.stream_id] = {
                                "request": {"headers": None, "body": None},
                                "complete": False,
                                "headers": "",
                                "body": b"",
                            }
                        headers = Parser.parse_header(frame.payload.decode())
                        self.recv_streams[frame.stream_id] = {
                            "headers": headers,
                            "body": b"",
                        }
                    if frame.flags == 1:
                        self.__complete_stream(frame.stream_id)
            except:
                self.connecting = False
                self.socket.close()
                break

    def __send_headers(self, stream_id, headers, end_stream=False):
        hdr = ""
        for header in headers:
            hdr += f"{header[0]}: {header[1]}\r\n"
        frame = Frame.create_headers_frame(stream_id, hdr.encode(), end_stream)
        self.send_buffers[stream_id] = [frame]

    def __send_body(self, stream_id, body):
        chunk_size = Frame.Frame.max_payload_size
        chunk_size = 1
        while len(body) > chunk_size:
            frame = Frame.create_data_frame(stream_id, body[:chunk_size])
            body = body[chunk_size:]
            self.send_buffers[stream_id].append(frame)
        frame = Frame.create_data_frame(stream_id, body, end_stream=True)
        self.send_buffers[stream_id].append(frame)

    def send_reqeuest(self, request):
        if not self.connecting:
            self.connect(self.host, self.port)

        stream_id = self.__get_next_stream_id()
        self.recv_streams[stream_id] = {
            "request": request,
            "complete": False,
            "headers": "",
            "body": b"",
        }
        headers = request["headers"]
        if "body" in request:
            self.__send_headers(stream_id, headers)
            body = request["body"]
            self.__send_body(stream_id, body)
        else:
            self.__send_headers(stream_id, headers, end_stream=True)
        return self.wait_for_response(stream_id)

    def get(self, url: str, stream=True):
        if url[:7] != "http://":
            url = "http://" + url
        urlo = urlparse(url)
        self.host = urlo.hostname
        self.port = urlo.port
        request = {
            "headers": [
                (":method", "GET"),
                (":path", urlo.path),
                (":scheme", "http"),
                (":authority", urlo.netloc),
            ]
        }
        return self.send_reqeuest(request)

    def close(self):
        self.connecting = False
        self.socket.close()


def write_file_from_response(file_path, response):
    if response:
        print(f"{file_path} begin")
        with open(file_path, "wb") as f:
            while True:
                content = response.get_stream_content()
                if content is None:
                    break
                f.write(content)
        print(f"{file_path} end")
    else:
        print("no response")


if __name__ == "__main__":
    client = HTTPClient()
    target_path = "../../target"
    response = client.get(url=f"127.0.0.1:8084/")
    file_list = []
    if response:
        headers = response.get_headers()
        if headers["content-type"] == "text/html":
            body = response.get_full_body()
            root = ET.fromstring(body.decode())
            links = root.findall(".//a")
            file_list = []
            for link in links:
                file_list.append(link.text)

    for file in glob.glob(os.path.join(target_path, "*.txt")):
        os.remove(file)

    th_list = []
    for file in file_list:
        response = client.get(f"127.0.0.1:8084/static/{file}")
        th = threading.Thread(
            target=write_file_from_response, args=[f"{target_path}/{file}", response]
        )
        th_list.append(th)
        th.start()

    for th in th_list:
        th.join()
