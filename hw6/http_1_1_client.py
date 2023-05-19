import socket
from Utils import Parser
import os
import glob
import xml.etree.ElementTree as ET
from urllib.parse import urlparse


class Response:
    def __init__(self, socket, stream) -> None:
        self.socket = socket
        self.stream = stream

        # fieleds
        self.version = ""  # e.g., "HTTP/1.1"
        self.status = ""  # e.g., "200 OK"
        self.headers = {}  # e.g., {content-type: application/json}
        self.body = b""  # e.g. "{'id': '123', 'key':'456'}"
        self.body_length = 0
        self.complete = False
        self.__reamin_bytes = b""

    def get_full_body(self):  # used for handling short body
        if self.stream or not self.complete:
            return None
        return self.body  # the full content of HTTP response body

    def get_stream_content(self):  # used for handling long body
        if not self.stream or self.complete:
            return None
        if self.body != b"":
            content = self.body
            self.body = b""
            return content
        content = self.get_remain_body()  # recv remaining body data from socket
        return content  # the part content of the HTTP response body

    def get_remain_body(self):
        if self.complete:
            return None
        recv_bytes = self.socket.recv(4096)
        self.body_length -= len(recv_bytes)
        if self.body_length == 0:
            self.complete = True
        return recv_bytes


class HTTPClient:
    def __init__(self, host="127.0.0.1", port=8080) -> None:
        self.connecting = False
        self.host = host
        self.port = port

    def send_reqeuest(self, request: str):
        if not self.connecting:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            try:
                self.socket.connect((self.host, self.port))
                self.connecting = True
            except:
                return None
        try:
            self.socket.sendall(request.encode())
        except:
            self.connecting = False
            self.socket.close()
            return None

        # Receive the server's response
        try:
            recv_bytes = self.socket.recv(4096)
            response = Parser.parse_response(recv_bytes.decode())
            if response is None:
                return None
        except:
            self.connecting = False
            self.socket.close()
            return None
        ret = Response(self.socket, True)
        ret.version = response["version"]
        ret.headers = response["headers"]
        ret.status = response["status"]
        ret.body = response["body"].encode()
        ret.body_length = int(response["headers"]["content-length"]) - len(ret.body)
        return ret

    def get(self, url: str, stream=True):
        if url[:7] != "http://":
            url = "http://" + url
        urlo = urlparse(url)
        self.host = urlo.hostname
        self.port = urlo.port
        request = f"GET {urlo.path} HTTP/1.0\r\n\r\n"
        return self.send_reqeuest(request)


if __name__ == "__main__":
    client = HTTPClient()

    target_path = "../../target"
    response = client.get(url=f"127.0.0.1:8081/")
    file_list = []
    if response and response.headers["content-type"] == "text/html":
        root = ET.fromstring(response.body.decode())
        links = root.findall(".//a")
        file_list = []
        for link in links:
            file_list.append(link.text)

    for file in glob.glob(os.path.join(target_path, "*.txt")):
        os.remove(file)

    for file in file_list:
        response = client.get(f"127.0.0.1:8081/static/{file}", stream=True)
        file_path = f"{target_path}/{file}"
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
