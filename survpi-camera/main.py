import os
import subprocess
import time
import socket

tempPath = "/home/pi/SurveillancePi/survpi-camera/current.h264"
streamStart = -1

def createLocalStream():
    return subprocess.Popen([
        "/usr/bin/libcamera-vid",
        "-t","0",
        "--width","1920",
        "--height","1080",
        "--codec","h264",
        "--inline",
        "--listen",
        "-v","0",
        "-o","tcp://0.0.0.0:8889"
    ],shell = True)

def createLocalReceiver(outputPath):
    return subprocess.Popen([
        "/usr/bin/su","pi","-c",
        "cd /home/pi/SurveillancePi/survpi-camera/ && /usr/bin/cvlc tcp/h264://0.0.0.0:8889 --sout=file/ps:" + outputPath
    ])

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
    try:
        os.remove(tempPath)
    except FileNotFoundError:
        pass
    print("[MAIN - INFO] Starting local stream...")
    cameraProcess = createLocalStream()
    print("[MAIN - INFO] Starting local receiver...")
    vlcProcess = createLocalReceiver(tempPath)
    streamStart = time.time()

    lastFileLength = 0
    masterSocket.send(b"survpi-camera!reset-cache")
    while True:
        currentTime = time.time()
        if (currentTime - streamStart >= 300):
            vlcProcess.terminate()
            cameraProcess.wait()
            vlcProcess.wait()
            print("[MAIN - OK] Stream restarting.")
            break

        if (vlcProcess.poll() != None or cameraProcess.poll() != None):
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

            masterSocket.send(newData)

            lastFileLength = currentFileLength

    print("[MAIN - OK] Reached end, reconnecting socket.")
    masterSocket.close()
    masterSocket = connectSocket(masterSocketAddress)