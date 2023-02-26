import socketserver
import socket
import signal
import multiprocessing
import time

class SocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        pass


def broadcastThread():
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    try:
        while True:
            udpSocket.sendto(b"survpi-master!ready-recv",("192.168.178.255",8887))
            time.sleep(3)
            print("sent ping")
    except KeyboardInterrupt:
        udpSocket.close()

if (__name__ == "__main__"):
    udpBroadcaster = multiprocessing.Process(
        target = broadcastThread
    )
    udpBroadcaster.start()

    tcpServer = socketserver.TCPServer(("0.0.0.0",8888),SocketHandler)
    tcpServer.serve_forever()