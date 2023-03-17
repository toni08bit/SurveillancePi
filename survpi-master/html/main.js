var scriptElements = undefined

function onInit() {
    let topbarPlaceholderElement = document.getElementById("topbar-placeholder")
    if (topbarPlaceholderElement) {
        console.log("[TOPBAR] Fetching...")
        fetch(
            "/page/topbar.html"
        ).then(function(response) {
            if (!response.ok) {
                alert("[ERROR/FATAL] Failed to fetch topbar!")
                location.reload()
                return
            }
            response.text().then(function(responseText) {
                document.body.replaceChild(((new DOMParser()).parseFromString(responseText,"text/html")).getElementById("topbar"),topbarPlaceholderElement)
                console.log("[TOPBAR] Finished.")

                let fileName = window.location.pathname.split("/")
                fileName = fileName[fileName.length - 1]
                scriptElements = {
                    "topbar-refreshtime": document.getElementById("topbar-refreshtime")
                }
                if (fileName == "" || fileName == "index.html") {
                    scriptElements["camera-cards-container"] = document.getElementById("camera-cards")
                    getDataJson(function(dataJson) {
                        topbarRefreshTime(dataJson)
                        loadCameras(dataJson)
                    })
                } else if (fileName == "save.html") {
                    scriptElements["save-from-date"] = document.getElementById("save-from-date")
                    scriptElements["save-from-time"] = document.getElementById("save-from-time")
                    scriptElements["save-until-date"] = document.getElementById("save-until-date")
                    scriptElements["save-until-time"] = document.getElementById("save-until-time")
                    scriptElements["save-submit"] = document.getElementById("save-submit")
                    scriptElements["save-status"] = document.getElementById("save-status")
                    getDataJson(function(dataJson) {
                        topbarRefreshTime(dataJson)
                    })
                    scriptElements["save-submit"].addEventListener("click",function(event) {
                        if (scriptElements["save-from-date"].value == "" || scriptElements["save-from-time"].value == "" || scriptElements["save-until-date"].value == "" || scriptElements["save-until-time"].value == "") {
                            alert("Fill in all the fields.")
                            return
                        }
                        if (!confirm("Are you sure?")) {
                            return
                        }

                        let startDate = (new Date(scriptElements["save-from-date"].value))
                        let startTime = scriptElements["save-from-time"].value.split(":")
                        startDate.setHours(startTime[0])
                        startDate.setMinutes(startTime[1])
                        let endDate = (new Date(scriptElements["save-until-date"].value))
                        let endTime = scriptElements["save-until-time"].value.split(":")
                        endDate.setHours(endTime[0])
                        endDate.setHours(endTime[1])

                        scriptElements["save-submit"].innerText = "Please wait..."
                        scriptElements["save-submit"].setAttribute("disabled",true)

                        fetch(
                            "/job",
                            {
                                "method": "POST",
                                "body": JSON.stringify({
                                    "name": "pack",
                                    "start": (startDate.valueOf() / 1000),
                                    "end": (endDate.valueOf() / 1000)
                                })
                            }
                        ).then(function(response) {
                            if (!response.ok) {
                                alert("Failed to submit request! Please try again later.")
                                return
                            }
                            response.text().then(function(responseText) {
                                alert("The request has been submitted.")
                                scriptElements["save-status"].innerText = ("Request ID: " + responseText + ", check Requests page.")
                            })
                        })
                    })
                } else if (fileName == "requests.html") {
                    scriptElements["response-list"] = document.getElementById("response-list")
                    getDataJson(function(dataJson) {
                        topbarRefreshTime(dataJson)
                        loadResponses(dataJson)
                    })
                } else {
                    console.warn("Unknown page: " + fileName)
                }
            })
        })
    }
}

function getDataJson(callbackFunc) {
    fetch(
        "/data"
    ).then(function(response) {
        if (!response.ok) {
            alert("[ERROR] Could not load data.json")
            return
        }
        response.text().then(function(responseText) {
            if (responseText == "" || responseText == "{}") {
                console.warn("[WARN] data.json is empty. Not calling back.")
                return
            }
            callbackFunc(JSON.parse(responseText))
        })
    })
}

function getDataCsv(callbackFunc) {
    fetch(
        "/data"
    ).then(function(response) {
        if (!response.ok) {
            alert("[ERROR] Could not load data.csv")
            return
        }
        response.text().then(function(responseText) {
            let textLines = responseText.split("\n")
            let finalLines = []
            let isFirstLine = true
            for (let textLine of textLines) {
                if (isFirstLine) {
                    isFirstLine = false
                    continue
                }
                if (textLine == "") {
                    break
                }
                let splitLine = textLine.split(",")
                finalLines.push(splitLine)
            }
            callbackFunc(finalLines)
        })
    })
}

function topbarRefreshTime(dataJson) {
    let updateDifference = ((Date.now() / 1000) - dataJson.fileUpdate) / 60
    scriptElements["topbar-refreshtime"].innerText = (String(Math.round(updateDifference)) + "min")
}

function createCameraCard(cameraObject,cameraName) {
    let currentTime = Date.now() / 1000

    let newContainer = document.createElement("div")
    newContainer.setAttribute("class","card camera-card")
    let thumbnailContainer = document.createElement("div")
    thumbnailContainer.setAttribute("class","camera-card-thumbnail-container")
    newContainer.appendChild(thumbnailContainer)
    let thumbnailImg = document.createElement("img")
    thumbnailImg.setAttribute("src",("data:image/jpeg;base64," + cameraObject.thumbnail))
    thumbnailContainer.appendChild(thumbnailImg)
    let nameSpan = document.createElement("span")
    nameSpan.setAttribute("class","camera-card-name")
    nameSpan.innerText = cameraName
    newContainer.appendChild(nameSpan)
    let hostSpan = document.createElement("span")
    hostSpan.setAttribute("class","camera-card-host")
    hostSpan.innerText = cameraObject.host
    newContainer.appendChild(hostSpan)
    let timeSpan = document.createElement("span")
    timeSpan.setAttribute("class","camera-card-time")
    timeSpan.innerText = (String(Math.round((currentTime - cameraObject.lastReset) / 60 * 10) / 10) + "min")
    newContainer.appendChild(timeSpan)
    
    scriptElements["camera-cards-container"].appendChild(newContainer)
}

function loadCameras(dataJson) {
    let cameraId = 1
    for (let camera of dataJson.connectedCameras) {
        createCameraCard(camera,("Camera #" + String(cameraId)))
        cameraId = cameraId + 1
    }
}

function createResponseItem(responseObject) {
    // TODO
}

function loadResponses(dataJson) {
    for (let responseObject of dataJson.jobs) {
        createResponseItem(responseObject)
    }
}