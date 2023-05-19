import socket
import threading
from datetime import datetime
import json
from hashlib import sha256
import hmac
import base64
import random


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
        self.version = "HTTP/1.1"
        self.alive = True
        self.key = hmac_sha256(f"key{random.random()*100}", "http11")
        self.thread = threading.Thread(target=self.__handle_loop)
        self.thread.start()

    def __parse_reqeust(self, request):
        # Split the request into a list of strings
        lines = request.split("\r\n")

        # Split the method, resource and version
        request_list = lines[0].split()

        # Extract method and requested resource
        method = request_list[0]
        resource = request_list[1]
        version = request_list[2]

        # Split resource into path and parameters
        resource = resource.split("?")
        if len(resource) == 2:
            path, parameters = resource
        else:
            path = resource[0]
            parameters = ""

        # Split the parameters into list
        parameters = parameters.split("&")

        # Initialize an empty dictionary to store the params
        params = {}

        # Iterate through the parameters
        for para in parameters:
            # Split the para into a key-value pair
            para = para.split("=")
            if len(para) == 2:
                key, value = para
                params[key] = value

        # Initialize an empty dictionary to store the headers
        headers = {}

        # Iterate through the lines
        for line in lines[1:]:
            # Skip empty lines
            if line == "":
                break
            # Split the line into a key-value pair
            line = line.split(": ")
            if len(line) == 2:
                key, value = line
                headers[key] = value

        # Extract the body (if any)
        body = ""
        if "\r\n\r\n" in request:
            body = request.split("\r\n\r\n")[1]

        return method, path, params, version, headers, body

    def __handle_loop(self):
        while self.alive:
            try:
                # Recv request
                request = self.client.recv(4096)
                print(request)

                # check connection
                if request == "":
                    self.alive = False
                    self.client.close()
                    break

                if self.version == "HTTP/1.1":
                    # parse request
                    method, path, params, version, headers, body = self.__parse_reqeust(
                        request.decode()
                    )
                    if (
                        "Connection" in headers
                        and "Upgrade" in headers
                        and "HTTP2-Settings" in headers
                    ):
                        connection = headers["Connection"].replace(" ", "").split(",")
                        if "Upgrade" in connection and headers["Upgrade"] == "h2c":
                            self.version = "HTTP/2.0"
                elif self.version == "HTTP/2.0":
                    method, path, params, version, headers, body = self.__parse_reqeust(
                        request.decode()
                    )
                    print("hi")
                    pass

                status = 200
                # Check the method and path
                if method == "GET":
                    if path == "/":
                        response = "HTTP/1.1 200 OK\r\n"
                        response += "Connection: keep-alive\r\n"
                        response += "Content-Type: text/html\r\n\r\n"
                        response += (
                            "<html><body>" + "<h1>HTTP 1.0</h1>" + "</body></html>"
                        )
                    elif path == "/get":
                        if "id" in params:
                            response = "HTTP/1.1 200 OK\r\n"
                            response += "Connection: keep-alive\r\n"
                            response += "Content-Type: application/json\r\n\r\n"
                            response += json.dumps(
                                {"id": params["id"], "key": self.key}
                            )
                        else:
                            response = "HTTP/1.1 200 OK\r\n"
                            response += "Connection: keep-alive\r\n"
                            response += "Content-Type: application/json\r\n\r\n"
                            response += json.dumps({"id": "", "key": ""})
                    else:
                        status = 404
                        response = "HTTP/1.1 404 Not Found\r\n"
                        response += "Connection: keep-alive\r\n"
                        response += "Content-Type: text/html\r\n\r\n"
                        response += "<html><body><h1>404 Not Found</h1></body></html>"
                elif method == "POST":
                    if path == "/post":
                        if (
                            "Content-Type" in headers
                            and headers["Content-Type"] == "application/json"
                        ):
                            try:
                                data = json.loads(body)
                            except:
                                data = None
                        else:
                            data = None
                        if data:
                            if (
                                "id" in data
                                and "key" in data
                                and data["key"] == self.key
                            ):
                                response = "HTTP/1.1 200 OK\r\n"
                                response += "Connection: keep-alive\r\n"
                                response += "Content-Type: application/json\r\n\r\n"
                                response += json.dumps({"success": True})
                            else:
                                response = "HTTP/1.1 200 OK\r\n"
                                response += "Connection: keep-alive\r\n"
                                response += "Content-Type: application/json\r\n\r\n"
                                response += json.dumps({"success": False})
                        else:
                            status = 400
                            response = "HTTP/1.1 400 Bad Request\r\n"
                            response += "Connection: keep-alive\r\n"
                            response += "Content-Type: text/html\r\n\r\n"
                            response += (
                                "<html><body><h1>400 Bad Request</h1></body></html>"
                            )
                    else:
                        status = 404
                        response = "HTTP/1.1 404 Not Found\r\n"
                        response += "Connection: keep-alive\r\n"
                        response += "Content-Type: text/html\r\n\r\n"
                        response += "<html><body><h1>404 Not Found</h1></body></html>"
                else:
                    status = 400
                    response = "HTTP/1.1 400 Bad Request\r\n"
                    response += "Connection: keep-alive\r\n"
                    response += "Content-Type: text/html\r\n\r\n"
                    response += "<html><body><h1>400 Bad Request</h1></body></html>"

                # Send the response to the client
                self.client.sendall(response.encode())

                # Log
                print(
                    f'{self.address[0]} - - {datetime.now().strftime("%d/%m/%y %H:%M:%S")} "{method} {path} {version}" {status} -'
                )

                # Close the connection with the client
                if version == "HTTP/1.0" and not (
                    "Connection" in headers and headers["Connection"] == "keep-alive"
                ):
                    self.alive = False
                    self.client.close()
                    break
            except:
                self.alive = False
                self.client.close()
                break

    def close(self):
        self.alive = False
        self.client.close()


class HttpServer:
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
                pass

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
    server = HttpServer()
    server.run()

    while True:
        cmd = input()
        if cmd == "close" or cmd == "exit":
            server.close()
            break
