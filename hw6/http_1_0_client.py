import socket
import json
from Utils import Parser


class http_1_0_client:
    pass


def send_reqeuest(request, host="127.0.0.1", port=8080):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((host, port))
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
    except:
        s.close()
        return None
    s.close()
    return response


if __name__ == "__main__":
    # Send an HTTP GET request to the server
    request = "GET /get?id=123 HTTP/1.0\r\n\r\n"
    response = send_reqeuest(request)
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
    request = f"POST /post HTTP/1.0\r\nContent-Type: application/json\r\n\r\n{json.dumps(data)}"
    response = send_reqeuest(request)
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
