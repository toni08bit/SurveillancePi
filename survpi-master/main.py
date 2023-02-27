import socketserver
import socket
import json
import multiprocessing
import time

configFile = "/home/pi/SurveillancePi/survpi-master/config.json"
pendingData = {}

class SocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        print(f"[{self.client_address}] Blocking...")
        self.data = self.request.recv()
        if (self.data == b"survpi-camera!ready-send"):
            print(f"[{self.client_address}] Ready.")
            pendingData[self.client_address] = b""
        else:
            if (not pendingData.get(self.client_address)):
                print(f"[{self.client_address}] Closing, no entry.")
                self.connection.close()
                return
            print(f"[{self.client_address}] Appending {str(len(self.data))} bytes.")
            pendingData[self.client_address] = pendingData[self.client_address] + self.data
    
    def finish(self):
        if (not pendingData.get(self.client_address)):
            print(f"[{self.client_address}] Ignoring disconnect, no entry.")
            return
        print(f"[{self.client_address}] Disconnected with {str(len(pendingData[self.client_address]))} bytes.")


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
                    if (exception.errno != 101):
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