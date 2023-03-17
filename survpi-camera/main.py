import os
import subprocess
import time
import socket

import survpiprotocol

tempPath = "/home/pi/SurveillancePi/survpi-camera/current.mp4"
thumbnailTempPath = "/home/pi/SurveillancePi/survpi-camera/thumbnail.jpg"
streamStart = -1

def createRecorder(outputPath):
    return subprocess.Popen([
        "/usr/bin/libcamera-vid",
        "-t","0",
        "--width","1920",
        "--height","1080",
        "--codec","libav",
        "-n",
        "-o",outputPath
    ])

def takeThumbnail():
    pictureProcess = subprocess.Popen([
        "/usr/bin/libcamera-still",
        "-t","2000",
        "--width","1920",
        "--height","1080",
        "-n",
        "-o",thumbnailTempPath
    ])
    pictureProcess.wait()
    openFile = open(thumbnailTempPath,"rb")
    readData = openFile.read()
    openFile.close()
    return readData

def locateMasterSocket():
    udpSocket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    udpSocket.bind(("0.0.0.0",8887))
    while True:
        data,originAddress = udpSocket.recvfrom(1024)
        if (data == b"survpi-master!ready-recv"):
            return (originAddress[0],8888)

def connectSocket(address):
    newSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    newSocket.connect(address)
    return newSocket

print("[MAIN - INFO] Locating master socket...")
masterSocketAddress = locateMasterSocket()
print("[MAIN - INFO] Connecting to master socket...")
masterSocket = connectSocket(masterSocketAddress)

print("[MAIN - OK] Beginning stream cycle.")
while True:
    print("[MAIN - INFO] Taking thumbnail...")
    survpiprotocol.send(masterSocket,"t",takeThumbnail())

    try:
        os.remove(tempPath)
    except FileNotFoundError:
        pass
    print("[MAIN - INFO] Starting recorder...")
    recorderProcess = createRecorder(tempPath)
    streamStart = time.time()

    lastFileLength = 0
    survpiprotocol.send(masterSocket,"r")
    while True:
        currentTime = time.time()
        if (currentTime - streamStart >= 900):
            recorderProcess.terminate()
            recorderProcess.wait()
            print("[MAIN - OK] Stream restarting.")
            break

        if (recorderProcess.poll() != None):
            recorderProcess.terminate()
            recorderProcess.wait()
            print("[MAIN - ERROR] Process died.")
            time.sleep(1)
            break

        try:
            currentFileLength = os.stat(tempPath).st_size
        except FileNotFoundError:
            continue

        if (currentFileLength > lastFileLength):
            currentFile = open(tempPath,"rb")
            currentFile.seek(lastFileLength)
            newData = currentFile.read(currentFileLength - lastFileLength)
            currentFile.close()

            survpiprotocol.send(masterSocket,"f",newData)

            lastFileLength = currentFileLength

        time.sleep(0.2)

    print("[MAIN - OK] Reached end, reconnecting socket.")
    masterSocket.close()
    masterSocket = connectSocket(masterSocketAddress)