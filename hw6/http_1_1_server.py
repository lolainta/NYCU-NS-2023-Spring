import socket
import threading
from datetime import datetime
import json
from hashlib import sha256
import hmac
import base64
import random
from Utils import Parser


def hmac_sha256(data, key):
    key = key.encode("utf-8")
    message = data.encode("utf-8")
    sign = base64.b64encode(hmac.new(key, message, digestmod=sha256).digest())
    sign = str(sign, "utf-8")
    return sign


class ClientHandler:
    def __init__(self, client, address) -> None:
        self.client = client
        self.client.settimeout(5)
        self.address = address
        self.alive = True
        self.key = hmac_sha256(f"key{random.random()*100}", "http11")
        self.recv_thread = threading.Thread(target=self.__recv_loop)
        self.recv_thread.start()

    def __bad_request_response(self):
        response = {
            "version": "HTTP/1.1",
            "status": "400 Bad Request",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><body><h1>400 Bad Request</h1></body></html>",
        }
        return response

    def __not_found_response(self):
        response = {
            "version": "HTTP/1.1",
            "status": "404 Not Found",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><body><h1>404 Not Found</h1></body></html>",
        }
        return response

    def __do_get(self, request):
        path = request["path"]
        params = request["params"]
        response = self.__not_found_response()
        if path == "/":
            response["status"] = "200 OK"
            response["headers"] = {"Content-Type": "text/html"}
            response["body"] = "<html><body>" + "<h1>HTTP 1.0</h1>" + "</body></html>"
        elif path == "/get":
            if "id" in params:
                response["status"] = "200 OK"
                response["headers"] = {"Content-Type": "application/json"}
                response["body"] = json.dumps({"id": params["id"], "key": self.key})
            else:
                response["status"] = "200 OK"
                response["headers"] = {"Content-Type": "application/json"}
                response["body"] = json.dumps({"id": "", "key": ""})
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
        response_str = f"{response['version']} {response['status']}\r\n"

        for key in response["headers"]:
            response_str += f"{key}: {response['headers'][key]}\r\n"
        response_str += f"\r\n{response['body']}"

        self.client.sendall(response_str.encode())

        # Log
        print(
            f"{self.address[0]} - - {datetime.now().strftime('%d/%m/%y %H:%M:%S')} \"{request['method']} {request['path']} {request['version']}\" {response['status']} -"
        )

    def __recv_loop(self):
        while self.alive:
            try:
                # Recv request
                recv_bytes = self.client.recv(4096)

                # check connection
                if not recv_bytes:
                    self.alive = False
                    self.client.close()
                    break

                # parse request
                request = Parser.parse_reqeust(recv_bytes.decode())
                print(request)
                if request == None:
                    method = ""
                else:
                    method = request["method"]
                # Check the method and path
                if method == "GET":
                    self.__do_get(request)
                elif method == "POST":
                    self.__do_post(request)
                else:
                    self.__send_response(request, self.__bad_request_response())

                # keep connection: don't close socket

            except:
                self.alive = False
                self.client.close()
                break

    def close(self):
        self.alive = False
        self.client.close()


class HttpServer_1_1:
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

                client_handler = ClientHandler(client, address)

                for handler in reversed(self.handler_list):
                    if not handler.alive:
                        self.handler_list.remove(handler)
                self.handler_list.append(client_handler)

            except:
                # catch socket closed
                self.alive = False

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
    server = HttpServer_1_1()
    server.run()

    while True:
        cmd = input()
        if cmd == "close" or cmd == "exit":
            server.close()
            break
