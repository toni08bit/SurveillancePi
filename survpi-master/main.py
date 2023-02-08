import socketserver

class SocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        pass


if (__name__ == "__main__"):
    tcpServer = socketserver.TCPServer(("0.0.0.0",8888),SocketHandler)
    tcpServer.serve_forever()