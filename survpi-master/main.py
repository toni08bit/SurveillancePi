import socket
import json
import multiprocessing
import subprocess
import time
import shutil
import uuid
import base64
import os
import importlib

survpiprotocol = importlib.import_module("/home/pi/SurveillancePi/modules/survpiprotocol.py")

configFile = "/home/pi/SurveillancePi/survpi-master/config.json"
dataCsvFile = "/home/pi/SurveillancePi/survpi-master/files/data.csv"
dataJsonFile = "/home/pi/SurveillancePi/survpi-master/data.json"
jobsJsonFile = "/home/pi/SurveillancePi/survpi-master/jobs.json"
externalFolder = "/media/survpi-output/"
internalFolder = "/home/pi/SurveillancePi/survpi-master/files/"

processData = {
    "lastStart": time.time()
}

class AcceptedConnection:
    def __init__(self,connection,address):
        self.pendingDataFile = None
        self.lastReset = -1
        self.lastPacket = -1
        self.connection = connection
        self.address = address
        self.thumbnail = None

        self.connection.setblocking(False)

def workConnections():
    for connectedClient in tcpConnections:
        receivedData = survpiprotocol.recv(connectedClient.connection)
        if (receivedData[1] == -1):
            continue
        elif (receivedData[1] == 1):
            connectedClient.pendingDataFile = None
            connectedClient.lastReset = time.time()
            while True:
                if ((connectedClient.pendingDataFile != None) and (not getFilePath(connectedClient.pendingDataFile)[0])):
                    break
                connectedClient.pendingDataFile = str(uuid.uuid4()) + ".h264"
            print(f"[{connectedClient.address[0]}] Reset.")
        elif (receivedData[1] == 2):
            if (connectedClient.pendingDataFile == None):
                print(f"[{connectedClient.address[0]}] Closing, no entry.")
                connectedClient.connection.close()
                tcpConnections.remove(connectedClient)
                return
            appendFilePart(connectedClient.pendingDataFile,receivedData[0])
            connectedClient.lastPacket = time.time()
        elif (receivedData[1] == 3):
            connectedClient.thumbnail = receivedData[0]
        elif (receivedData[1] == 0):
            connectedClient.connection.close()
            tcpConnections.remove(connectedClient)
            print(f"[{connectedClient.address[0]}] Disconnected. Saving...")
            if ((connectedClient.lastReset == -1) or (connectedClient.lastPacket == -1)):
                print(f"[{connectedClient.address[0]}] No packet or not reset.")
                continue
            
            dataFileSize = os.stat(getFilePath(connectedClient.pendingFilePath)[0]).st_size
            openFile = open(dataCsvFile,"a")
            openFile.write(f"{connectedClient.pendingDataFile},{connectedClient.address[0]}:{str(connectedClient.address[1])},{str(connectedClient.lastReset)},{str(time.time())},{str(dataFileSize)}\n")
            openFile.flush()
            openFile.close()

            print(f"[{connectedClient.address[0]}] Saved {str(dataFileSize)} bytes.")
            connectedClient.pendingDataFile = None
                
    updateDataJson()

def getConfigData():
    openFile = open(configFile,"r")
    configData = json.loads(openFile.read())
    openFile.close()
    return configData

def getFilePath(fileName):
    if (os.path.isfile(externalFolder + fileName)):
        return (externalFolder + fileName),1
    elif (os.path.isfile(internalFolder + fileName)):
        return (internalFolder + fileName),0
    else:
        return None,-1

def appendFilePart(fileName,data):
    openFile = None
    pathResult = getFilePath(fileName)
    if ((os.path.isdir(externalFolder))):
        if (pathResult[1] == 0):
            shutil.move(pathResult[0],(externalFolder + fileName))
            print("[MAIN - OK] Moved file " + fileName + " to external.")
        
        openFile = open((externalFolder + fileName),"ab")
    else:
        openFile = open((internalFolder + fileName),"ab")
    
    openFile.write(data)
    openFile.flush()
    openFile.close()

def updateDataJson():
    preparedData = {
        "connectedCameras": [],
        "lastStart": processData["lastStart"]
    }

    for connectedClient in tcpConnections:
        preparedData["connectedCameras"].append({
            "host": connectedClient.address[0],
            "port": connectedClient.address[1],
            "pendingFile": connectedClient.pendingDataFile,
            "lastPacket": connectedClient.lastPacket
        })

    openFile = open(dataJsonFile,"w")
    openFile.write(json.dumps(preparedData))
    openFile.flush()
    openFile.close()

def runJob(jobData):
    jobObject = base64.b64decode(json.loads(jobData))
    jobName = jobObject.get("name")
    if (jobName == ""):
        pass # TODO jobs

def readJobsJson():
    openFileRead = open(jobsJsonFile,"r")
    readData = openFileRead.read()
    openFileRead.close()
    if (len(readData) <= 2):
        return
    readDataJson = json.loads(readData)
    for jobData in readDataJson:
        runJob(jobData)
    openFileWrite = open(jobsJsonFile,"w")
    openFileWrite.write("{}")
    openFileWrite.close()

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
            if (len(tcpConnections) < 5):
                try:
                    connection,address = tcpServer.accept()
                    tcpConnections.append(AcceptedConnection(connection,address))
                    print(f"[{address[0]}] Accepted.")
                except BlockingIOError:
                    pass
            if (len(tcpConnections) > 0):
                workConnections()
            else:
                time.sleep(0.05)
    except KeyboardInterrupt:
        udpBroadcaster.terminate()
        webHoster.terminate()
        tcpServer.close()