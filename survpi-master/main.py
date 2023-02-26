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
            udpSocket.sendto(b"survpi-master!ready-recv",("",8887))
            time.sleep(10)
    except KeyboardInterrupt:
        udpSocket.close()
        print("Closed UDP socket")

if (__name__ == "__main__"):
    udpBroadcaster = multiprocessing.Process(
        target = broadcastThread
    )
    udpBroadcaster.start()

    tcpServer = socketserver.TCPServer(("255.255.255.255",8888),SocketHandler)
    tcpServer.serve_forever()