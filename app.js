mapboxgl.accessToken = 'pk.eyJ1IjoibmFmaXpyYWhhbWFuIiwiYSI6ImNtbWY4NngzNjA1bm4yb29mYmNxY3BpOXgifQ.c5N3qAkFPCXOvcRnEn-5JQ';

const map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11',
    center: [0, 20],
    zoom: 1.5,
    projection: 'globe' // Display as a 3D globe
});

map.on('style.load', () => {
    map.setFog({
        color: 'rgb(13, 15, 18)', // Lower atmosphere
        'high-color': 'rgb(0, 243, 255)', // Upper atmosphere
        'horizon-blend': 0.02, // Atmosphere thickness
        'space-color': 'rgb(2, 4, 8)', // Background color
        'star-intensity': 0.6 // Background star brightness
    });
});

let hoveredStateId = null;

map.on('load', () => {

    // 1. Add Countries Source
    map.addSource('countries', {
        type: 'geojson',
        data: 'data/countries.geojson',
        generateId: true
    });

    // 2. Add Subregions Source
    map.addSource('subregions', {
        type: 'geojson',
        data: 'data/subregions.geojson',
        generateId: true
    });

    // --- COUNTRIES LAYER ---
    map.addLayer({
        'id': 'countries-fill',
        'type': 'fill',
        'source': 'countries',
        'layout': {
            'visibility': 'visible'
        },
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'SUM_Biolog'], // Assuming SUM_Biolog is the stat, fallback if null
                0, 'rgba(0, 243, 255, 0.1)',
                100, 'rgba(0, 243, 255, 0.8)'
            ],
            'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.8,
                0.4
            ]
        }
    });

    map.addLayer({
        'id': 'countries-line',
        'type': 'line',
        'source': 'countries',
        'layout': {
            'visibility': 'visible'
        },
        'paint': {
            'line-color': '#00f3ff',
            'line-width': 0.5
        }
    });

    // --- SUBREGIONS LAYER ---
    map.addLayer({
        'id': 'subregions-fill',
        'type': 'fill',
        'source': 'subregions',
        'layout': {
            'visibility': 'none'
        },
        'paint': {
            'fill-color': [
                'interpolate',
                ['linear'],
                ['get', 'SUM_Biolog'],
                0, 'rgba(255, 0, 234, 0.1)',
                100, 'rgba(255, 0, 234, 0.8)'
            ],
            'fill-opacity': [
                'case',
                ['boolean', ['feature-state', 'hover'], false],
                0.8,
                0.4
            ]
        }
    });

    map.addLayer({
        'id': 'subregions-line',
        'type': 'line',
        'source': 'subregions',
        'layout': {
            'visibility': 'none'
        },
        'paint': {
            'line-color': '#ff00ea',
            'line-width': 1
        }
    });

    // --- INTERACTIVITY ---

    function setupHover(layerId, sourceName, nameField) {
        map.on('mousemove', layerId, (e) => {
            if (e.features.length > 0) {
                if (hoveredStateId !== null) {
                    map.setFeatureState(
                        { source: sourceName, id: hoveredStateId },
                        { hover: false }
                    );
                }
                hoveredStateId = e.features[0].id;
                map.setFeatureState(
                    { source: sourceName, id: hoveredStateId },
                    { hover: true }
                );

                const props = e.features[0].properties;
                const name = props[nameField] || 'Unknown Region';

                // You can change SUM_Biolog to whichever stat is critical in your shapefile
                const val = props['SUM_Biolog'] !== undefined ? props['SUM_Biolog'] : 'N/A';

                document.getElementById('feature-info').innerHTML = `
                    <h3 style="color:var(--neon-blue); margin-bottom:5px;">${name}</h3>
                    <p><strong>Predicted Metadata (Bio):</strong> <span class="neon-pink">${val}</span></p>
                `;
            }
        });

        map.on('mouseleave', layerId, () => {
            if (hoveredStateId !== null) {
                map.setFeatureState(
                    { source: sourceName, id: hoveredStateId },
                    { hover: false }
                );
            }
            hoveredStateId = null;
            document.getElementById('feature-info').innerHTML = '<p class="placeholder-text">Hover over the map to see specific region insights.</p>';
        });
    }

    setupHover('countries-fill', 'countries', 'REGION_UN');
    setupHover('subregions-fill', 'subregions', 'SUBREGION');

    // --- BUTTON CONTROLS ---

    document.getElementById('btn-countries').addEventListener('click', function () {
        this.classList.add('active');
        document.getElementById('btn-subregions').classList.remove('active');

        map.setLayoutProperty('countries-fill', 'visibility', 'visible');
        map.setLayoutProperty('countries-line', 'visibility', 'visible');
        map.setLayoutProperty('subregions-fill', 'visibility', 'none');
        map.setLayoutProperty('subregions-line', 'visibility', 'none');
    });

    document.getElementById('btn-subregions').addEventListener('click', function () {
        this.classList.add('active');
        document.getElementById('btn-countries').classList.remove('active');

        map.setLayoutProperty('subregions-fill', 'visibility', 'visible');
        map.setLayoutProperty('subregions-line', 'visibility', 'visible');
        map.setLayoutProperty('countries-fill', 'visibility', 'none');
        map.setLayoutProperty('countries-line', 'visibility', 'none');
    });

});
