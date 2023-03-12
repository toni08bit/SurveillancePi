import struct

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
    
    dataLength = struct.unpack("<i",_force_recv(connection,4))[0]
    receivedData = _force_recv(connection,dataLength)
    return (receivedData,dataType)

def send(connection,dataType,data = None):
    if (data and isinstance(data,str)):
        data = bytes(data,"utf-8")
        
    if (dataType == "r"):
        connection.sendall(b"r")
        return
    elif (dataType == "f"):
        packet = b"f"
    elif (dataType == "t"):
        packet = b"t"

    packet = packet + struct.pack("<i",len(data))
    packet = packet + data

    connection.sendall(packet)


def _force_recv(connection,dataLength):
    connection.setblocking(True)
    missingBytes = dataLength
    receivedData = b""
    while missingBytes > 0:
        newData = connection.recv(missingBytes)
        receivedData = receivedData + newData
        missingBytes = missingBytes - len(newData)
    connection.setblocking(False)
    return receivedData