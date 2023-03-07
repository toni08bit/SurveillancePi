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
    
    dataLength = struct.unpack("<i",connection.recv(4))
    print("recv: " + str(dataLength))
    return (connection.recv(dataLength),dataType)

def send(connection,dataType,data = None):
    if (data and isinstance(data,str)):
        data = bytes(data,"utf-8")
        
    packet = b""
    if (dataType == "r"):
        packet = packet + b"r"
        connection.send(packet)
        return
    elif (dataType == "f"):
        packet = packet + b"f"
    elif (dataType == "t"):
        packet = packet + b"t"

    packet = packet + struct.pack("<i",len(data))
    packet = packet + data
    connection.send(packet)