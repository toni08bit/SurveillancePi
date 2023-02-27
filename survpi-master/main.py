import socketserver
import socket
import json
import multiprocessing
import time

configFile = "/home/SurveillancePi/survpi-master/config.json"

class SocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        self.data = self.request.recv(1024)
        self.client_address


def getConfigData():
    openFile = open(configFile)
    configData = json.loads(openFile.read())
    openFile.close()
    return configData

def broadcastThread():
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    try:
        while True:
            configData = getConfigData()
            if (configData.get("doBroadcast")):
                try:
                    udpSocket.sendto(b"survpi-master!ready-recv",("192.168.178.255",8887))
                except OSError as exception:
                    if (exception.errno != 101): # not Network unreachable
                        raise
            time.sleep(configData.get("broadcastInterval"))
    except KeyboardInterrupt:
        udpSocket.close()

if (__name__ == "__main__"):
    udpBroadcaster = multiprocessing.Process(
        target = broadcastThread
    )
    udpBroadcaster.start()

    tcpServer = socketserver.TCPServer(("0.0.0.0",8888),SocketHandler)
    tcpServer.serve_forever()