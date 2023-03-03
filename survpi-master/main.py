import socket
import json
import multiprocessing
import subprocess
import time
import uuid
import os

configFile = "/home/pi/SurveillancePi/survpi-master/config.json"
dataCsvFile = "/home/pi/SurveillancePi/survpi-master/files/data.csv"

class AcceptedConnection:
    def __init__(self,connection,address):
        self.pendingDataFile = None
        self.lastReset = -1
        self.status = None
        self.connection = connection
        self.address = address

        self.connection.setblocking(False)

def workConnections():
    for connectedClient in tcpConnections:
        try:
            receivedData = connectedClient.connection.recv(8192)
            if (receivedData == b"survpi-camera!reset-cache"):
                connectedClient.pendingDataFile = None
                connectedClient.lastReset = time.time()
                while True:
                    if ((connectedClient.pendingDataFile != None) and (not os.path.isfile(connectedClient.pendingDataFile))):
                        break
                    connectedClient.pendingDataFile = "/home/pi/SurveillancePi/survpi-master/files/" + str(uuid.uuid4()) + ".h264"
                print(f"[{connectedClient.address[0]}] Reset.")
            elif (not receivedData):
                connectedClient.connection.close()
                tcpConnections.remove(connectedClient)
                print(f"[{connectedClient.address[0]}] Disconnected. Saving...")
                if ((not os.path.isfile(connectedClient.pendingDataFile)) or (connectedClient.lastReset == -1)):
                    print(f"[{connectedClient.address[0]}] No pending data or not reset.")
                    continue
                
                dataFileSize = os.stat(connectedClient.pendingDataFile).st_size
                openFile = open(dataCsvFile,"a")
                openFile.write(f"{connectedClient.pendingDataFile},{connectedClient.address[0]}:{str(connectedClient.address[1])},{str(connectedClient.lastReset)},{str(time.time())},{str(dataFileSize)}\n")
                openFile.flush()
                openFile.close()

                print(f"[{connectedClient.address[0]}] Saved {str(dataFileSize)} bytes.")
                connectedClient.pendingDataFile = None
            else:
                if (connectedClient.pendingDataFile == None):
                    print(f"[{connectedClient.address[0]}] Closing, no entry.")
                    connectedClient.connection.close()
                    tcpConnections.remove(connectedClient)
                    return
                openFile = open(connectedClient.pendingDataFile,"ab")
                openFile.write(receivedData)
                openFile.flush()
                openFile.close()
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

def webSubprocess():
    return subprocess.Popen([
        "/home/pi/SurveillancePi/survpi-master/.env/bin/uwsgi",
        "--ini","/home/pi/SurveillancePi/survpi-master/web.ini"
    ])


if (__name__ == "__main__"):
    print("[MAIN - INFO] Starting web subprocess...")
    webHoster = webSubprocess()

    print("[MAIN - INFO] Starting broadcaster thread...")
    udpBroadcaster = multiprocessing.Process(
        target = broadcastThread
    )
    udpBroadcaster.start()

    print("[MAIN - OK] Starting main tcp socket...")
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
        webHoster.terminate()
        tcpServer.close()