import flask
import json
import base64
import os

application = flask.Flask("survpi-web")
dataJsonFile = "/home/pi/SurveillancePi/survpi-master/data.json"
jobsJsonFile = "/home/pi/SurveillancePi/survpi-master/jobs.json"

@application.route("/",methods = ["GET"])
def index():
    return flask.send_file("html/index.html"),200

@application.route("/page/<path:path>",methods = ["GET"])
def page(path):
    finalPath = os.path.abspath("html/" + path)
    if (not finalPath.startswith("/home/pi/SurveillancePi/survpi-master/html/")):
        return "None of your business",403
    return flask.send_file(finalPath),200

@application.route("/data",methods = ["GET"])
def data():
    dataJson = _getDataJson()
    if (dataJson == None):
        return "Not available",503
    return dataJson,200

@application.route("/job",methods = ["POST"])
def job():
    _addJob(flask.request.json)

def _getDataJson():
    openFile = open(dataJsonFile,"r")
    readData = openFile.read()
    openFile.close()
    if (len(readData) <= 2):
        return None
    return json.loads(readData)

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
    currentJobData = _getJobsJson()
    currentJobData.append(base64.b64encode(json.dumps(jobObject)))
    _setJobsJson(currentJobData)

if (__name__ == "__main__"):
    application.run()