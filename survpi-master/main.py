import socketserver
import socket
import json
import multiprocessing
import time

configFile = "/home/pi/SurveillancePi/survpi-master/config.json"
pendingData = {}

class SocketHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            self.connection
            print(f"[{self.client_address}] Blocking...")
            self.data = self.request.recv(2048)
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

class AcceptedConnection:
    def __init__(self,connection,address):
        self.pendingData = b""
        self.status = None
        self.connection = connection
        self.address = address

        self.connection.setblocking(False)

def workConnections():
    for connectedClient in tcpConnections:
        try:
            receivedData = connectedClient.connection.recv(4096)
            if (receivedData == b"survpi-camera!reset-cache"):
                pendingData[connectedClient.address] = b""
                print(f"[{connectedClient.address[0]}] Reset.")
            elif (not receivedData):
                connectedClient.connection.close()
                tcpConnections.remove(connectedClient)
                print(f"[{connectedClient.address[0]}] Disconnected. Saving...")
                if (pendingData.get(connectedClient.address) == None):
                    print(f"[{connectedClient.address[0]}] No pending data.")
                    continue
                # TODO actually save
                print(f"[{connectedClient.address[0]}] Saved {str(len(pendingData[connectedClient.address]))} bytes.")
                pendingData[connectedClient.address] = None
            else:
                if (pendingData.get(connectedClient.address) == None):
                    print(f"[{connectedClient.address[0]}] Closing, no entry.")
                    connectedClient.connection.close()
                    tcpConnections.remove(connectedClient)
                    return
                print(f"[{connectedClient.address[0]}] Appending {str(len(receivedData))} bytes.")
                pendingData[connectedClient.address] = pendingData[connectedClient.address] + receivedData
        except BlockingIOError:
            pass

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
    print("[MAIN] Starting Threads and Sockets.")
    udpBroadcaster = multiprocessing.Process(
        target = broadcastThread
    )
    udpBroadcaster.start()

    tcpConnections = []
    tcpServer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpServer.bind(("0.0.0.0",8888))
    tcpServer.setblocking(False)
    tcpServer.listen(5)
    try:
        while True:
            try:
                connection,address = tcpServer.accept()
                tcpConnections.append(AcceptedConnection(connection,address))
                print(f"[{address[0]}] Accepted.")
            except BlockingIOError:
                pass

            workConnections()

            
    except KeyboardInterrupt:
        udpBroadcaster.terminate()
        tcpServer.close()