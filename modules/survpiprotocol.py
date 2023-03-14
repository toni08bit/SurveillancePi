import struct
import socket

def recv(connection):
    try:
        dataType = connection.recv(1)
    except BlockingIOError:
        return ("",-1)
    
    if (dataType == b"r"): # RESET
        return ("",1)
    elif (dataType == b"f"): # FRAME
        dataType = 2
    elif (dataType == b"t"): # THUMBNAIL
        dataType = 3
    else:
        return ("",0)
    
    try:
        dataLength = struct.unpack("<i",_force_recv(connection,4))[0]
        receivedData = _force_recv(connection,dataLength)
        return (receivedData,dataType)
    except socket.timeout:
        return ("",0)

def send(connection,dataType,data = None):
    if (dataType == "r"):
        _force_send(connection,b"r")
        return
    elif (dataType == "f"):
        _force_send(connection,b"f")
    elif (dataType == "t"):
        _force_send(connection,b"t")

    _force_send(connection,struct.pack("<i",len(data)))
    _force_send(connection,data)

def _force_recv(connection,dataLength):
    connection.setblocking(True)
    connection.settimeout(20)
    missingBytes = dataLength
    receivedData = b""
    while missingBytes > 0:
        newData = connection.recv(missingBytes)
        receivedData = receivedData + newData
        missingBytes = missingBytes - len(newData)
    connection.setblocking(False)
    return receivedData

def _force_send(connection,data):
    dataLength = len(data)
    missingBytes = dataLength
    while missingBytes > 0:
        sentBytes = connection.send(data[(dataLength - missingBytes):])
        missingBytes = missingBytes - sentBytes