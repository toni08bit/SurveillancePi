import flask
import json
import base64
import zipfile
import io
import os

application = flask.Flask("survpi-web")
dataJsonFile = "/home/pi/SurveillancePi/survpi-master/data.json"
dataCsvFile = "/home/pi/SurveillancePi/survpi-master/files/data.csv"
jobsJsonFile = "/home/pi/SurveillancePi/survpi-master/jobs.json"
externalFolder = "/media/survpi-output/"
internalFolder = "/home/pi/SurveillancePi/survpi-master/files/"

@application.route("/",methods = ["GET"])
def index():
    return flask.send_file("html/index.html"),200

@application.route("/page/<path:path>",methods = ["GET"])
def page(path):
    finalPath = os.path.abspath("html/" + path)
    if (not finalPath.startswith("/home/pi/SurveillancePi/survpi-master/html/")):
        return "None of your business",403
    if (not os.path.isfile(finalPath)):
        return "Not found!",404
    return flask.send_file(finalPath),200

@application.route("/data",methods = ["GET"])
def data():
    dataJson = _getDataJson()
    if (dataJson == None):
        return "Not available",503
    return dataJson,200

@application.route("/data.csv",methods = ["GET"])
def datacsv():
    return flask.send_file(dataCsvFile),200

@application.route("/save",methods = ["GET"])
def save():
    startTime = flask.request.args["start"]
    endTime = flask.request.args["end"]
    if ((not isinstance(startTime,int)) or (not isinstance(endTime,int))):
        return "Invalid arguments",400
    timeData = _readDataCsv()
    includedFiles = []
    for line in timeData:
        currentStart = int(line[2])
        currentEnd = int(line[3])
        if (currentStart <= endTime and currentEnd >= startTime):
            includedFiles.append(line)

    zipBytes = io.BytesIO()
    newZip = zipfile.ZipFile(zipBytes,"w",zipfile.ZIP_DEFLATED)
    for includedFile in includedFiles:
        getFileResult = _getFilePath(includedFile[0])
        if (not getFileResult):
            print("[WEB - WARN] File " + includedFile[0] + " requested, but not available! Skipping...")
            continue
        arcName = (includedFile[1].replace(".","-") + "/" + includedFile[2] + "-" + includedFile[3])
        newZip.write(getFileResult,arcName)

@application.route("/job",methods = ["POST"])
def job():
    _addJob(flask.request.json)

def _getDataJson():
    openFile = open(dataJsonFile,"r")
    readData = openFile.read()
    openFile.close()
    return readData

def _getJobsJson():
    openFile = open(jobsJsonFile,"r")
    readData = openFile.read()
    openFile.close()
    return json.loads(readData)

def _setJobsJson(jobsObject):
    openFile = open(jobsJsonFile,"w")
    openFile.write(json.dumps(jobsObject))
    openFile.flush()
    openFile.close()

def _readDataCsv():
    openFile = open(dataCsvFile,"r")
    readData = openFile.readlines()
    openFile.close()

    finalList = []
    for lineKey in range(1,len(readData)):
        lineValue = readData[lineKey]
        finalList.append(lineValue.split(","))

    return finalList

def _getFilePath(fileName):
    if (os.path.isfile(externalFolder + fileName)):
        return (externalFolder + fileName)
    else:
        if (os.path.isfile(internalFolder + fileName)):
            return (internalFolder + fileName)
        else:
            return None

def _addJob(jobObject):
    currentJobData = _getJobsJson()
    currentJobData.append(base64.b64encode(json.dumps(jobObject)))
    _setJobsJson(currentJobData)

if (__name__ == "__main__"):
    application.run()