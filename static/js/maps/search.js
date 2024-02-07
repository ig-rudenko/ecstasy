document.getElementById("searchInput")
    .addEventListener("keyup", (e) => {
        e.preventDefault();
        if (e.keyCode === 13) {
            searchPoint(e.target.value)
        }
    })

document.getElementById("searchButton")
    .addEventListener("click", (e) => {
        searchPoint(document.getElementById("searchInput").value)
    })


function highlightMarker(marker) {
    if (!marker.options._originFillColor) {
        marker.options._originFillColor = marker.options.fillColor
    }

    for (let i = 1; i <= 20; i++) {
        setTimeout(() => {
            marker._path.style.fill = i % 2 === 0 ? marker.options._originFillColor : "orange";
            marker._path.style.fill = i % 2 === 0 ? marker.options._originFillColor : "orange";
        }, 250*i)
    }

    setTimeout(() => marker._path.style.fill = marker.options._originFillColor, 5100)
}

function searchPoint(text) {
    if (!text || String(text).length < 4) return;
    text = String(text).toLowerCase()
    let marker = null
    for (const point of points) {
        let name = point[1].point.feature.properties.name
        let desc = point[1].point.feature.properties.description
        if (name.toLowerCase().includes(text) || desc.toLowerCase().includes(text)) {
            console.log(point[1])
            if (!marker) {
                map.flyTo(point[1].point._latlng, 17)
                marker = point[1]
            }
            highlightMarker(point[1].point)
        }
    }
    return marker;
}