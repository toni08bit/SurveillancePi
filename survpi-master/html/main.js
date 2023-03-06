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
            })
        })
    }
}