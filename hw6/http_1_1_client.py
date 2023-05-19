import socket
import json
from Utils import Parser


class HTTPClient:
    def __init__(self, host="127.0.0.1", port=8080) -> None:
        self.connecting = False
        self.host = host
        self.port = port

    def send_reqeuest(self, request):
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
            self.connecting = True
            self.socket.close()
            return None

        # Receive the server's response
        try:
            recv_bytes = self.socket.recv(4096)
            response = Parser.parse_response(recv_bytes.decode())
        except:
            self.connecting = True
            self.socket.close()
            return None

        return response


if __name__ == "__main__":
    client = HTTPClient()

    request = "GET /get?id=123 HTTP/1.1\r\n\r\n"
    response = client.send_reqeuest(request)
    print(response)
    headers = response["headers"]
    body = response["body"]

    if "content-type" in headers and headers["content-type"] == "application/json":
        try:
            data = json.loads(body)
            if "id" in data and "key" in data:
                print(f"Get id={data['id']} key={data['key']}")
            else:
                data = None
        except:
            data = None
    else:
        data = None

    if data is None:
        print("Get failed")
        exit()

    # Send an HTTP POST request to the server
    request = f"POST /post HTTP/1.1\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}"
    response = client.send_reqeuest(request)
    print(response)
    headers = response["headers"]
    body = response["body"]
    if "content-type" in headers and headers["content-type"] == "application/json":
        try:
            data = json.loads(body)
            if "success" in data:
                print(f"Post success={data['success']}")
            else:
                data = None
        except:
            data = None
    else:
        data = None
    if not data:
        print("Post failed")
