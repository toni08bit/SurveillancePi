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
    
    connection.setblocking(True)
    dataLength = struct.unpack("<i",connection.recv(4))[0]
    missingBytes = dataLength
    receivedData = b""
    while missingBytes > 0:
        receivedData = receivedData + connection.recv(missingBytes)
        missingBytes = missingBytes - len(receivedData)
    connection.setblocking(False)
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