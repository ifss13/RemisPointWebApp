// En el archivo index.html, dentro de la sección <script>

async function getCoordinates(address) {
    // Utiliza una API de geocodificación como Nominatim para obtener las coordenadas
    const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`);
    const data = await response.json();
    return [data[0].lat, data[0].lon];
}

async function getRoute(origin, destination) {
    const originCoords = await getCoordinates(origin);
    const destinationCoords = await getCoordinates(destination);

    // Reemplaza 'TU_API_KEY' con tu clave API de OpenRouteService
    const response = await fetch(`https://api.openrouteservice.org/v2/directions/driving-car?api_key=5b3ce3597851110001cf6248bbaa88fc959c42db9efc751597c03a47&start=${originCoords.join(',')}&end=${destinationCoords.join(',')}`);
    const data = await response.json();

    const route = data.features[0].geometry.coordinates;
    return route;
}

async function calculateRoute() {
    const origin = document.getElementById('origin').value;
    const destination = document.getElementById('destination').value;

    const route = await getRoute(origin, destination);

    L.polyline(route, {color: 'blue'}).addTo(map);
}