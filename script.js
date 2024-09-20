const API_URL = 'http://100.26.236.1:5001';
let authToken = null;

async function makeApiRequest(endpoint, method, data = null) {
    const url = `${API_URL}${endpoint}`;
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();
        document.getElementById('response').innerHTML = `<pre>${JSON.stringify(result, null, 2)}</pre>`;
        
        if (endpoint === '/login' && response.ok) {
            authToken = result.access_token;
            updateButtonStates();
        }
    } catch (error) {
        document.getElementById('response').innerHTML = `<pre>Error: ${error.message}</pre>`;
    }
}

function updateButtonStates() {
    const authButtons = document.querySelectorAll('button[disabled]');
    authButtons.forEach(button => {
        button.disabled = !authToken;
    });
}

function getEndpointData(button) {
    const endpoint = button.closest('.endpoint');
    const path = endpoint.querySelector('.path').textContent.trim();
    const method = endpoint.querySelector('.method').textContent.trim();
    const inputs = endpoint.querySelectorAll('input');
    const data = {};
    inputs.forEach(input => {
        data[input.id.split('-').pop()] = input.value;
    });
    return { path, method, data };
}

function getRandomCoordinates() {
    const lat = (Math.random() * 180 - 90).toFixed(6);
    const lon = (Math.random() * 360 - 180).toFixed(6);
    return { lat, lon };
}

function addLocationHandler() {
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                document.getElementById('latitude').value = position.coords.latitude.toFixed(6);
                document.getElementById('longitude').value = position.coords.longitude.toFixed(6);
            },
            (error) => {
                console.error("Error getting location:", error);
                const { lat, lon } = getRandomCoordinates();
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lon;
            }
        );
    } else {
        console.log("Geolocation is not available");
        const { lat, lon } = getRandomCoordinates();
        document.getElementById('latitude').value = lat;
        document.getElementById('longitude').value = lon;
    }
}

function submitBidHandler() {
    const serviceDescription = document.getElementById('service-description').value;
    const bidPrice = document.getElementById('bid-price').value;
    const latitude = document.getElementById('latitude').value;
    const longitude = document.getElementById('longitude').value;

    if (!serviceDescription || !bidPrice || !latitude || !longitude) {
        alert("Please fill in all fields");
        return;
    }

    const bidData = {
        service: serviceDescription,
        price: parseFloat(bidPrice),
        lat: parseFloat(latitude),
        lon: parseFloat(longitude),
        end_time: Math.floor(Date.now() / 1000) + 86400 // 24 hours from now
    };

    makeApiRequest('/make_bid', 'POST', bidData);
}

document.addEventListener('DOMContentLoaded', () => {
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', (event) => {
            const { path, method, data } = getEndpointData(event.target);
            makeApiRequest(path, method, Object.keys(data).length ? data : null);
        });
    });

    const addLocationButton = document.getElementById('add-location');
    if (addLocationButton) {
        addLocationButton.addEventListener('click', addLocationHandler);
    }

    const submitBidButton = document.getElementById('submit-bid');
    if (submitBidButton) {
        submitBidButton.addEventListener('click', submitBidHandler);
    }
});