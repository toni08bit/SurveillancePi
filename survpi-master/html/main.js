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

                } else if (fileName == "camera.html") {
                    scriptElements["camera-cards-container"] = document.getElementById("camera-cards")
                    getDataJson(function(dataJson) {
                        topbarRefreshTime(dataJson)
                        loadCameras(dataJson)
                    })
                } else if (fileName == "status.html") {

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

function createCameraCard(cameraObject) {
    let newContainer = document.createElement("div")
    newContainer.setAttribute("class","card camera-card")
    let thumbnailContainer = document.createElement("div")
    thumbnailContainer.setAttribute("class","camera-card-thumbnail-container")
    newContainer.appendChild(thumbnailContainer)
    let thumbnailImg = document.createElement("img")
    thumbnailImg.setAttribute("src",("data:image/jpeg;base64," + cameraObject.thumbnail))
    thumbnailContainer.appendChild(thumbnailImg)
    
    scriptElements["camera-cards-container"].appendChild(newContainer)
}

function loadCameras(dataJson) {
    for (let camera of dataJson.connectedCameras) {
        createCameraCard(camera)
    }
}

function topbarRefreshTime(dataJson) {
    scriptElements["topbar-refreshtime"].innerText = (String(((Date.now() / 1000) - dataJson.fileUpdate) / 60) + "min")
}