import socket
import threading
import json
import time
from Utils import Frame
from Utils import Parser
from QUIC import quic_client


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
            try:
                self.socket.connect((host, port))

                self.connecting = True
                self.recv_buffer = b""
                self.recv_streams = {}
                self.next_stream_id = 1
                self.recv_thread = threading.Thread(target=self.__recv_loop)
                self.recv_thread.start()
            except:
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
                except:
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
                stream_id, recv_bytes = self.socket.recv()
                # print(stream_id, recv_bytes)
                if not stream_id:
                    self.connecting = False
                    self.socket.close()
                    break
                # parse response
                response = Parser.parse_response(recv_bytes.decode())
                self.recv_streams[stream_id] = {"complete": True, "response": response}
            except:
                self.connecting = False
                self.socket.close()
                break

    def send_reqeuest(self, request):
        if not self.connecting:
            return
        stream_id = self.__get_next_stream_id()
        self.socket.send(stream_id, request.encode())
        self.recv_streams[stream_id] = {
            "complete": False,
            "request": request,
            "response": {},
        }
        return stream_id

    def close(self):
        self.connecting = False
        self.socket.close()


if __name__ == "__main__":
    client = HTTPClient()
    client.connect()

    request = "GET /get?id=123 HTTP/3.0\r\n\r\n"

    stream_id_1 = client.send_reqeuest(request)
    stream_id_2 = client.send_reqeuest(request)
    response = client.wait_for_response(stream_id_1)
    data = json.loads(response["body"])
    print(stream_id_1, response)
    response = client.wait_for_response(stream_id_2)
    print(stream_id_2, response)
    headers = [
        (":method", "POST"),
        (":path", "/post"),
        (":scheme", "http"),
        (":authority", "127.0.0.1:8080"),
        ("content-type", "application/json"),
    ]
    request = f"POST /post HTTP/3.0\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}"
    stream_id_3 = client.send_reqeuest(request)
    response = client.wait_for_response(stream_id_3)
    print(stream_id_3, response)

    client.close()
