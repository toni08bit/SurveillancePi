import flask
import json
import base64
import uuid
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

@application.route("/job",methods = ["POST"])
def job():
    return _addJob(flask.request.json),200

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

def _addJob(jobObject):
    jobObject["id"] = str(uuid.uuid4())
    currentJobData = _getJobsJson()
    if (currentJobData == {}):
        currentJobData = []
    currentJobData.append(base64.b64encode(bytes(json.dumps(jobObject),"utf-8")).decode("utf-8"))
    _setJobsJson(currentJobData)
    return jobObject["id"]

if (__name__ == "__main__"):
    application.run()