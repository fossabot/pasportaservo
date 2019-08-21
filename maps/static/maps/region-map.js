// @source: https://github.com/tejo-esperanto/pasportaservo/blob/master/maps/static/maps/region-map.js
// @license magnet:?xt=urn:btih:0b31508aeb0634b347b8270c7bee4d411b5d4109&dn=agpl-3.0.txt AGPL v3


window.addEventListener("load", function() {

    var container = document.getElementById('map');
    var location = container.hasAttribute('data-coordinates') ? container.getAttribute('data-coordinates') : '';
    try {
        location = location.trim() ? JSON.parse(location): undefined;
    }
    catch (e) {
        location = undefined;
    }
    if (location === undefined)
        return;

    mapboxgl.setRTLTextPlugin(GIS_ENDPOINTS['rtl_plugin']);

    var map = new mapboxgl.Map({
        container: container.id,
        style: GIS_ENDPOINTS['region_map_style'],
        pitchWithRotate: false,
        minZoom: 1.5,
        maxZoom: 15,
        center: location.center,
        maxBounds: [location.bbox.southwest, location.bbox.northeast],
    }).jumpTo({center: location.center});
    var labels = [];

    map.on('load', function() {
        var nav = new mapboxgl.NavigationControl();
        map.addControl(nav, 'top-left');

        map.addSource("region_hosts", {
            type: "geojson",
            data: GIS_ENDPOINTS['region_map_data'],
        });

        map.addLayer({
            id: "places",
            type: "circle",
            source: "region_hosts",
            paint: {
                "circle-color": [
                    "case",
                    ["get", "checked"],
                        ["case", ["get", "in_book"], "#4f9e4f", "#5cb85c"],
                    ["get", "confirmed"],
                        ["case", ["get", "in_book"], "#2b699b", "#337ab7"],
                    // not checked and not confirmed:
                        ["case", ["get", "in_book"], "#d69a46", "#f0ad4e"],
                ],
                "circle-radius": 6,
                "circle-stroke-width": 1,
                "circle-stroke-color": "#fff",
            }
        });
        map.on('click', 'places', function(e) {
            var placePanel = document.getElementById('p-' + e.features[0].id);
            if (!placePanel)
                return;
            placePanel.scrollIntoView();
            placePanel.className += ' highlight';
            setTimeout(function() {
                placePanel.className = placePanel.className.replace(/( +)highlight\b/g, '');
            }, 1200);
        });

        // Change the cursor to a pointer when the mouse is over the places layer.
        map.on('mouseenter', 'places', function(e) {
            map.getCanvas().style.cursor = "pointer";
            labels.push(
                new mapboxgl.Popup({ closeButton: false, className: 'supervisor-view' })
                    .setLngLat(e.features[0].geometry.coordinates)
                    .setHTML(e.features[0].properties.owner_full_name)
                    .addTo(map)
            );
        });

        // Change it back to a hand when it leaves.
        map.on('mouseleave', 'places', function(e) {
            map.getCanvas().style.cursor = "";
            while (labels.length) {
                labels.pop().remove();
            }
        });
    });

    window.mapObject = map;

});


// @license-end
