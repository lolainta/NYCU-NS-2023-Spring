import socket
import threading
from datetime import datetime
import json
from hashlib import sha256
import hmac
import base64
import random
from Utils import Frame
from Utils import Parser
import os
import io


def hmac_sha256(data, key):
    key = key.encode("utf-8")
    message = data.encode("utf-8")
    sign = base64.b64encode(hmac.new(key, message, digestmod=sha256).digest())
    sign = str(sign, "utf-8")
    return sign


class ClientHandler:
    def __init__(self, client: socket.socket, address, static) -> None:
        self.static = static
        self.client = client
        self.client.settimeout(5)
        self.address = address
        self.alive = True
        self.recv_buffer = b""
        self.recv_streams = {}
        self.send_buffers = {}
        self.key = hmac_sha256(f"key{random.random()*100}", "http20")
        self.recv_thread = threading.Thread(target=self.__recv_loop)
        self.recv_thread.start()
        self.send_thread = threading.Thread(target=self.__send_loop)
        self.send_thread.start()

    def __bad_request_response(self):
        response = {
            "version": "HTTP/2.0",  # e.g. "HTTP/2.0"
            "status": "400 Bad Request",  # e.g. "200 OK"
            "headers": {
                "Content-Type": "text/html"
            },  # e.g. {content-type: application/json}
            "body": "<html><body><h1>400 Bad Request</h1></body></html>",
        }
        return response

    def __not_found_response(self):
        response = {
            "version": "HTTP/2.0",  # e.g. "HTTP/2.0"
            "status": "404 Not Found",  # e.g. "200 OK"
            "headers": {
                "Content-Type": "text/html"
            },  # e.g. {content-type: application/json}
            "body": "<html><body><h1>404 Not Found</h1></body></html>",
        }
        return response

    def __do_get(self, request):
        path = request["path"]
        params = request["params"]
        response = self.__not_found_response()
        files = os.listdir(self.static)
        if path == "/":
            response["status"] = "200 OK"
            files = random.sample(files, k=3)
            response[
                "body"
            ] = """
            <html>
                <header></header>
                <body>
                    <a href="/static/{0}">{0}</a>
                    <br/>
                    <a href="/static/{1}">{1}</a>
                    <br/>
                    <a href="/static/{2}">{2}</a>
                </body>
            </html>
            """.format(
                *files
            )
            response["headers"] = {
                "Content-Type": "text/html",
                "Content-Length": len(request["body"]),
            }
        elif path == "/get":
            if "id" in params and len(self.recv_streams) > 1:
                response["status"] = "200 OK"
                response["headers"] = {"Content-Type": "application/json"}
                response["body"] = json.dumps({"id": params["id"], "key": self.key})
            else:
                response["status"] = "200 OK"
                response["headers"] = {"Content-Type": "application/json"}
                response["body"] = json.dumps({"id": "", "key": ""})
        elif path[:8] == "/static/":
            if path[8:] in files:
                response["status"] = "200 OK"
                content = ""
                with io.open(os.path.join(self.static, path[8:]), "r", newline="") as f:
                    content = f.readlines()
                content = "".join(content)
                response["body"] = content
                response["headers"] = {
                    "Content-Type": "Content-Type: text/plain",
                    "Content-Length": len(content),
                }
        else:
            print(path)
        self.__send_response(request, response)

    def __do_post(self, request):
        path = request["path"]
        headers = request["headers"]
        response = self.__not_found_response()
        if path == "/post":
            if (
                "content-type" in headers
                and headers["content-type"] == "application/json"
            ):
                try:
                    post_data = json.loads(request["body"])
                except:
                    post_data = None
            else:
                post_data = None
            if post_data:
                if (
                    "id" in post_data
                    and "key" in post_data
                    and post_data["key"] == self.key
                ):
                    response["status"] = "200 OK"
                    response["headers"] = {"Content-Type": "application/json"}
                    response["body"] = json.dumps({"success": True})
                    print(post_data["id"], "success")
                else:
                    response["status"] = "200 OK"
                    response["headers"] = {"Content-Type": "application/json"}
                    response["body"] = json.dumps({"success": False})
                    print(post_data["id"], "fail")
            else:
                response = self.__bad_request_response()
        self.__send_response(request, response)

    def __send_response(self, request, response):
        response["headers"][":status"] = response["status"]
        stream_id = request["stream_id"]
        self.__send_headers(stream_id, response["headers"])
        self.__send_body(stream_id, response["body"].encode())

        # Log
        print(
            f"{self.address[0]} - - {datetime.now().strftime('%d/%m/%y %H:%M:%S')} \"{request['method']} {request['path']} {request['version']}\" {response['status']} -"
        )

    def __send_headers(self, stream_id, headers, end_stream=False):
        hdr = ""
        for key in headers:
            hdr += f"{key.lower()}: {headers[key]}\r\n"
        frame = Frame.create_headers_frame(stream_id, hdr.encode(), end_stream)
        self.send_buffers[stream_id] = [frame]

    def __send_body(self, stream_id, body):
        chunk_size = Frame.Frame.max_payload_size
        while len(body) > chunk_size:
            frame = Frame.create_data_frame(stream_id, body[:chunk_size])
            body = body[chunk_size:]
            self.send_buffers[stream_id].append(frame)
        frame = Frame.create_data_frame(stream_id, body, end_stream=True)
        self.send_buffers[stream_id].append(frame)

    def __complete_request(self, stream_id):
        try:
            stream = self.recv_streams[stream_id]
            headers = stream["headers"]
            path, params = Parser.parse_resource(headers[":path"])
            request = {
                "stream_id": stream_id,
                "method": headers[":method"],  # e.g. "GET"
                "path": path,  # e.g. "/"
                "params": params,  # e.g. {'id': '123'}
                "scheme": headers[":scheme"],
                "version": "HTTP/2.0",  # e.g. "HTTP/1.0"
                "headers": stream["headers"],  # e.g. {content-type: application/json}
                "body": stream["body"].decode(
                    "utf-8"
                ),  # e.g. "{'id': params['id'], 'key': hmac_sha256(params['id'], 'http10')}"
            }
        except:
            if stream_id in self.recv_streams:
                del self.recv_streams[stream_id]
            return
        method = request["method"]
        # Check the method and path
        if method == "GET":
            self.__do_get(request)
        elif method == "POST":
            self.__do_post(request)
        else:
            self.__send_response(request, self.__bad_request_response())

    def __send_loop(self):
        while self.alive:
            try:
                end_streams = []
                keys = list(self.send_buffers.keys())
                for key in keys:
                    if len(self.send_buffers[key]) > 0:
                        frame = self.send_buffers[key].pop(0)
                        self.client.sendall(frame.to_bytes())
                        if frame.flags == 1:
                            end_streams.append(key)
                for key in end_streams:
                    del self.send_buffers[key]
            except:
                self.alive = False
                self.client.close()
                break

    def __recv_loop(self):
        while self.alive:
            try:
                # Recv request
                recv_bytes = self.client.recv(8192)
                # check connection
                if not recv_bytes:
                    self.alive = False
                    self.client.close()
                    break

                recv_bytes = self.recv_buffer + recv_bytes

                # parse request
                frames, remian_bytes = Frame.bytes_to_frames(recv_bytes)
                self.recv_buffer = remian_bytes
                for frame in frames:
                    if frame.type == 0:  # data
                        self.recv_streams[frame.stream_id]["body"] += frame.payload
                    elif frame.type == 1:  # header
                        headers = Parser.parse_header(frame.payload.decode())
                        self.recv_streams[frame.stream_id] = {
                            "headers": headers,
                            "body": b"",
                        }
                    if frame.flags == 1:
                        self.__complete_request(frame.stream_id)
            except:
                self.alive = False
                self.client.close()
                break

    def close(self):
        self.alive = False
        self.client.close()


class HTTPServer:
    def __init__(self, host="127.0.0.1", port=8080) -> None:
        # Create a socket object
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Bind the socket to a specific address and port
        self.socket.bind((host, port))

        # Listen for incoming connections
        self.socket.listen(5)

        # Create a thread to accept clients
        self.thread = threading.Thread(target=self.__accept_loop)

        self.alive = False

    def __accept_loop(self):
        while self.alive:
            try:
                # Establish a connection with the client
                client, address = self.socket.accept()
                print(client, address)

                client_handler = ClientHandler(client, address, self.static)

                for handler in reversed(self.handler_list):
                    if not handler.alive:
                        self.handler_list.remove(handler)
                self.handler_list.append(client_handler)
                print("accepted")
            except:
                # catch socket closed
                self.alive = False

    def set_static(self, static):
        self.static = static

    def run(self):
        if not self.alive:
            self.alive = True
            self.handler_list = []
            self.thread.start()

    def close(self):
        self.alive = False
        self.socket.close()
        self.thread.join()
        for handler in reversed(self.handler_list):
            if handler.alive:
                handler.close()


if __name__ == "__main__":
    server = HTTPServer(host="127.0.0.1", port=8084)
    server.set_static("../../static")
    server.run()

    while True:
        cmd = input()
        if cmd == "close" or cmd == "exit":
            server.close()
            break
