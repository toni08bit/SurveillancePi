import socket
import json
import multiprocessing
import subprocess
import time
import shutil
import uuid
import base64
import os
import zipfile

import survpiprotocol

configFile = "/home/pi/SurveillancePi/survpi-master/config.json"
dataCsvFile = "/home/pi/SurveillancePi/survpi-master/files/data.csv"
dataJsonFile = "/home/pi/SurveillancePi/survpi-master/data.json"
jobsJsonFile = "/home/pi/SurveillancePi/survpi-master/jobs.json"
externalFolder = "/media/survpi-output/"
internalFolder = "/home/pi/SurveillancePi/survpi-master/files/"

processData = {
    "lastStart": time.time(),
    "lastDataJsonUpdate": -1,
    "lastJobsJsonRead": -1,
    "jobResponse": [],
    "attemptedMount": False,
    "allowMount": False,
    "isMounted": False,
    "lastDiskUsageCheck": -1
}

class AcceptedConnection:
    def __init__(self,connection,address):
        self.pendingDataFile = None
        self.lastReset = -1
        self.lastPacket = time.time()
        self.connection = connection
        self.address = address
        self.thumbnail = None

        self.connection.setblocking(False)

def workConnections():
    currentTime = time.time()

    for connectedClient in tcpConnections:
        receivedData = survpiprotocol.recv(connectedClient.connection)
        if (receivedData[1] == -1):
            if ((currentTime - connectedClient.lastPacket) <= 120):
                continue
            
            print(f"[{connectedClient.address[0]}] Closing, timed out.")
            connectedClient.connection.close()
            tcpConnections.remove(connectedClient)
        elif (receivedData[1] == 1):
            connectedClient.pendingDataFile = None
            connectedClient.lastReset = currentTime
            while True:
                if ((connectedClient.pendingDataFile != None) and (not getFilePath(connectedClient.pendingDataFile)[0])):
                    break
                connectedClient.pendingDataFile = str(uuid.uuid4()) + ".h264"
            print(f"[{connectedClient.address[0]}] (Re)set.")
        elif (receivedData[1] == 2):
            if (connectedClient.pendingDataFile == None):
                print(f"[{connectedClient.address[0]}] Closing, no entry.")
                connectedClient.connection.close()
                tcpConnections.remove(connectedClient)
                continue
            appendFilePart(connectedClient.pendingDataFile,receivedData[0])
            connectedClient.lastPacket = currentTime
        elif (receivedData[1] == 3):
            connectedClient.thumbnail = receivedData[0]
        elif (receivedData[1] == 0):
            connectedClient.connection.close()
            tcpConnections.remove(connectedClient)
            print(f"[{connectedClient.address[0]}] Disconnected. Saving...")
            if ((connectedClient.lastReset == -1) or (connectedClient.lastPacket == -1)):
                print(f"[{connectedClient.address[0]}] No packet or not reset.")
                continue
            
            pathResult = getFilePath(connectedClient.pendingDataFile)[0]
            if (not pathResult):
                print(f"[{connectedClient.address[0]}] No file path.")
                continue
            dataFileSize = os.stat(pathResult).st_size
            
            openFile = open(dataCsvFile,"a")
            openFile.write(f"{connectedClient.pendingDataFile},{connectedClient.address[0]}:{str(connectedClient.address[1])},{str(round(connectedClient.lastReset))},{str(round(time.time()))},{str(dataFileSize)}\n")
            openFile.flush()
            openFile.close()

            print(f"[{connectedClient.address[0]}] Saved {str(dataFileSize)} bytes.")
            connectedClient.pendingDataFile = None
    
    if ((currentTime - processData["lastDataJsonUpdate"]) >= 10):
        updateDataJson()

    if ((currentTime - processData["lastJobsJsonRead"]) >= 1.5):
        readJobsJson()

def webSubprocess():
    return subprocess.Popen([
        "/home/pi/SurveillancePi/survpi-master/.env/bin/uwsgi",
        "--ini","/home/pi/SurveillancePi/survpi-master/web.ini"
    ])

def broadcastThread():
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    udpSocket.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
    try:
        while True:
            configData = getConfigData()
            if (configData.get("doBroadcast")):
                try:
                    udpSocket.sendto(b"survpi-master!ready-recv",(configData.get("broadcastAddress"),8887))
                except OSError as exception:
                    if (exception.errno != 101):
                        raise
            time.sleep(configData.get("broadcastInterval"))
    except KeyboardInterrupt:
        udpSocket.close()

def readJobsJson():
    processData["lastJobsJsonRead"] = time.time()
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

def addJobResponse(jobObject):
    if (not jobObject.get("expiresAt")):
        jobObject["expiresAt"] = time.time() + 900
    processData["jobResponse"].append(jobObject)

def getJobResponse():
    newJobResponse = []
    for job in processData["jobResponse"]:
        if (time.time() < job["expiresAt"]):
            newJobResponse.append(job)
    processData["jobResponse"] = newJobResponse
    return newJobResponse

def runJob(jobData):
    jobObject = json.loads(base64.b64decode(jobData).decode("utf-8"))
    jobName = jobObject.get("name")
    jobId = jobObject.get("id")
    if (jobName == "reboot"):
        os.system("reboot now")
    elif (jobName == "config"):
        if (jobObject.get("action") == "write"):
            openFile = open(configFile,"w")
            openFile.write(jobObject.get("data"))
            openFile.flush()
            openFile.close()
        else:
            openFile = open(configFile,"r")
            addJobResponse({
                "name": "config",
                "id": jobId,
                "data": json.loads(openFile.read())
            })
            openFile.close()
    elif (jobName == "pack"):
        timeData = readDataCsv()
        includedFiles = []
        for line in timeData:
            currentStart = int(line[2])
            currentEnd = int(line[3])
            if (currentStart <= jobObject.get("end") and currentEnd >= jobObject.get("start")):
                includedFiles.append(line)
        print("[INFO] Packing " + str(len(includedFiles)) + " files into zip " + jobId + ".")
        zipPath = (internalFolder + "packets/" + jobId + ".zip")
        zipBytes = open(zipPath,"ab")
        newZip = zipfile.ZipFile(zipBytes,"w",zipfile.ZIP_STORED)
        for includedFile in includedFiles:
            getFileResult = getFilePath(includedFile[0])[0]
            if (not getFileResult):
                print("[WARN] File " + includedFile[0] + " requested, but not available! Skipping...")
                continue
            arcName = (includedFile[1].replace(".","-") + "/" + includedFile[2] + "-" + includedFile[3])
            newZip.write(getFileResult,arcName)
        newZip.close()
        zipBytes.flush()
        zipBytes.close()
        addJobResponse({
            "name": "pack",
            "id": jobId,
            "status": 1
        })
        print("[OK] Packed zip " + jobId + ".")

def updateDataJson():
    currentTime = time.time()
    if ((currentTime - processData["lastDataJsonUpdate"]) < 1.5):
        return
    processData["lastDataJsonUpdate"] = currentTime

    preparedData = {
        "connectedCameras": [],
        "lastStart": processData["lastStart"],
        "jobs": getJobResponse(),
        "fileUpdate": time.time()
    }

    for connectedClient in tcpConnections:
        connectionObject = {
            "host": connectedClient.address[0],
            "port": connectedClient.address[1],
            "pendingFile": connectedClient.pendingDataFile,
            "lastPacket": connectedClient.lastPacket,
            "lastReset": connectedClient.lastReset
        }
        if (connectedClient.thumbnail):
            connectionObject["thumbnail"] = base64.b64encode(connectedClient.thumbnail).decode("utf8")

        preparedData["connectedCameras"].append(connectionObject)

    openFile = open(dataJsonFile,"w")
    openFile.write(json.dumps(preparedData))
    openFile.flush()
    openFile.close()

def getConfigData():
    openFile = open(configFile,"r")
    configData = json.loads(openFile.read())
    openFile.close()
    return configData

def readDataCsv():
    openFile = open(dataCsvFile,"r")
    readData = openFile.readlines()
    openFile.close()

    finalList = []
    for lineKey in range(1,len(readData)):
        lineValue = readData[lineKey]
        finalList.append(lineValue.split(","))

    return finalList

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

def getFilePath(fileName):
    if ((processData["isMounted"]) and ((time.time() - processData["lastDiskUsageCheck"]) > 15)):
        processData["lastDiskUsageCheck"] = time.time()
        manageDiskUsage()

    if (os.path.isfile(externalFolder + fileName)):
        processData["isMounted"] = True
        return (externalFolder + fileName),1
    else:
        if ((not processData["attemptedMount"]) and (processData["allowMount"]) and (not os.path.isdir(externalFolder))):
            print("[MAIN - INFO] Attempting to mount...")
            processData["attemptedMount"] = True
            mountCommand = getConfigData().get("mountCommand")
            mountProcess = subprocess.Popen(mountCommand)
            mountProcess.wait()
            return getFilePath(fileName)
        elif (os.path.isfile(internalFolder + fileName)):
            processData["isMounted"] = False
            return (internalFolder + fileName),0
        else:
            return None,-1

def getOldestFile():
    dataCsv = readDataCsv()
    lowestStartIndex = None
    for lineIndex in range(len(dataCsv)):
        lineValue = dataCsv[lineIndex]
        if ((lowestStartIndex == None) or (lineValue[2] < dataCsv[lowestStartIndex][2])):
            lowestStartIndex = lineIndex
    return dataCsv[lowestStartIndex][0]

def manageDiskUsage():
    configData = getConfigData()
    if (not configData.get("doAutoDelete")):
        return
    
    while True:
        _,_,freeSpace = shutil.disk_usage("/media")
        if (freeSpace > configData.get("diskMinFree")):
            break

        os.remove(getOldestFile())


if (__name__ == "__main__"):
    print("[MAIN - INFO] Reading config.json")
    configData = getConfigData()
    processData["allowMount"] = configData.get("doMount")

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
                time.sleep(0.15)
    except KeyboardInterrupt:
        udpBroadcaster.terminate()
        webHoster.terminate()
        tcpServer.close()