import threading
import time
from Utils import Parser
from QUIC import quic_client
from collections import deque
from urllib.parse import urlparse
import os
import glob
import threading
import xml.etree.ElementTree as ET


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
            self.socket = quic_client.QUICClient()
            self.socket.drop(5)
            try:
                self.socket.connect((host, port))
                self.connecting = True
                self.recv_buffer = b""
                self.recv_streams = {}
                self.next_stream_id = 1
                self.recv_thread = threading.Thread(target=self.__recv_loop)
                self.recv_thread.start()
            except Exception as e:
                print(e)
                self.connecting = False
                self.socket.close()

    def wait_for_response(self, stream_id):
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
                    response = self.recv_streams[stream_id]["response"]
                except Exception as e:
                    print(e)
                    response = None
                del self.recv_streams[stream_id]
                return response
            wait_count += 1
            time.sleep(0.01)
        del self.recv_streams[stream_id]
        return None

    def __recv_loop(self):
        while self.connecting:
            try:
                stream_id, recv_bytes, eos = self.socket.recv()
                assert stream_id is not None
                if not stream_id:
                    self.connecting = False
                    self.socket.close()
                    break
                # parse response
                if self.recv_streams[stream_id]["response"] is None:
                    resp = Parser.parse_response(recv_bytes.decode())
                    r = Response(stream_id)
                    r.headers = resp["headers"]
                    r.status = resp["status"]
                    r.contents.append(resp["body"].encode())
                    self.recv_streams[stream_id]["response"] = r
                else:
                    self.recv_streams[stream_id]["response"].contents.append(recv_bytes)
                if eos:
                    self.recv_streams[stream_id]["complete"] = True
                    self.recv_streams[stream_id]["response"].complete = True
            except Exception as e:
                print(e)
                self.connecting = False
                self.socket.close()
                break

    def send_reqeuest(self, request):
        if not self.connecting:
            self.connect(self.host, self.port)
        stream_id = self.__get_next_stream_id()
        self.recv_streams[stream_id] = {
            "complete": False,
            "request": request,
            "response": None,
        }
        headers = request["headers"]
        hdr = ""
        for header in headers:
            hdr += f"{header[0]}: {header[1]}\r\n"
        self.socket.send(stream_id, hdr.encode())
        return stream_id

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
        sid = self.send_reqeuest(request)
        while self.recv_streams[sid]["response"] is None:
            time.sleep(0.1)
            pass
        return self.recv_streams[sid]["response"]

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
    response = client.get(url=f"10.0.1.1:8080/")
    file_list = []
    if response:
        headers = response.get_headers()
        if not headers:
            exit()
        if headers["content-type"] == "text/html":
            body = response.get_full_body()
            if not body:
                exit()
            root = ET.fromstring(body.decode())
            links = root.findall(".//a")
            file_list = []
            for link in links:
                file_list.append(link.text)
    print(file_list)
    for file in glob.glob(os.path.join(target_path, "*.txt")):
        os.remove(file)

    th_list = []
    for file in file_list:
        response = client.get(f"10.0.1.1:8080/static/{file}")
        th = threading.Thread(
            target=write_file_from_response, args=[f"{target_path}/{file}", response]
        )
        th_list.append(th)
        th.start()

    for th in th_list:
        th.join()
    client.close()
