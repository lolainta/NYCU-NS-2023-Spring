from my.http_1_0_server import HTTPServer

if __name__ == '__main__':
    server = HTTPServer()
    server.set_static("../static")
    server.run()

    while True:
        cmd = input()
        if cmd == 'close' or cmd == 'exit':
            server.close()
            break