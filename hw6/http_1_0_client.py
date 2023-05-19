import socket
from Utils import Parser
from urllib.parse import urlparse

import xml.etree.ElementTree as ET
import os
import glob


class Response:
    def __init__(self, socket, stream) -> None:
        self.socket = socket
        self.stream = stream

        # fieleds
        self.version = ""  # e.g., "HTTP/1.0"
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
        recv_bytes = self.socket.recv(4096)
        if len(recv_bytes) == 0:
            self.complete = True
        return recv_bytes


class HTTPClient:  # For HTTP/1.X
    def __init__(self) -> None:
        pass

    def get(self, url, headers=None, stream=True):
        # Send the request and return the response (Object)
        # url = "http://127.0.0.1:8080/static/xxx.txt"
        # If stream=True, the response should be returned immediately after the full headers have been received.
        if url[:7] != "http://":
            url = "http://" + url
        url = urlparse(url)
        request = f"GET {url.path} HTTP/1.0\r\n\r\n"
        # response = send_reqeuest(request, host=url.hostname, port=url.port)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        try:
            s.connect((url.hostname, url.port))
        except:
            return None

        try:
            s.sendall(request.encode())
        except:
            s.close()
            return None
        # Receive the server's response
        try:
            recv_bytes = s.recv(4096)
            response = Parser.parse_response(recv_bytes.decode())
            ret = Response(s, True)
            ret.version = response["version"]
            ret.headers = response["headers"]
            ret.status = response["status"]
            ret.body = response["body"].encode()
        except:
            s.close()
            return None
        # s.close()
        return ret


if __name__ == "__main__":
    client = HTTPClient()
    target_path = "../../target"
    response = client.get(url="127.0.0.1:8080/")
    file_list = []
    if response and response.headers["content-type"] == "text/html":
        root = ET.fromstring(response.body.decode())
        links = root.findall(".//a")
        file_list = []
        for link in links:
            file_list.append(link.text)
    for file in glob.glob(os.path.join(target_path, "*.txt")):
        os.remove(file)
    print(file_list)
    for file in file_list:
        response = client.get(f"127.0.0.1:8080/static/{file}", stream=True)
        file_path = f"{target_path}/{file}"
        if response:
            print(response.headers)
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
