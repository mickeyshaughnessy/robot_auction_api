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
            updateUI();
        }
        return result;
    } catch (error) {
        document.getElementById('response').innerHTML = `<pre>Error: ${error.message}</pre>`;
    }
}

function updateUI() {
    const loginBtn = document.getElementById('login-btn');
    
    if (authToken) {
        loginBtn.textContent = 'Logout';
        fetchMyBids();
        fetchRecentBids();
    } else {
        loginBtn.textContent = 'Login';
        document.getElementById('my-bids').innerHTML = '';
        document.getElementById('recent-bids').innerHTML = '';
    }
}

async function fetchMyBids() {
    const result = await makeApiRequest('/my_bids', 'GET');
    if (result && result.bids) {
        const bidsHtml = result.bids.map(bid => `
            <div class="bid">
                <p>Service: ${bid.service}</p>
                <p>Price: $${bid.price}</p>
                <p>Status: ${bid.status}</p>
            </div>
        `).join('');
        document.getElementById('my-bids').innerHTML = bidsHtml;
    }
}

async function fetchRecentBids() {
    const { lat, lon } = getRandomCoordinates();
    const result = await makeApiRequest('/nearby', 'POST', { lat, lon });
    if (result && result.activities) {
        const bidsHtml = result.activities.map(bid => `
            <div class="bid">
                <p>Service: ${bid.service}</p>
                <p>Location: (${bid.lat.toFixed(4)}, ${bid.lon.toFixed(4)})</p>
            </div>
        `).join('');
        document.getElementById('recent-bids').innerHTML = bidsHtml;
    }
}

function getRandomCoordinates() {
    const lat = (Math.random() * 180 - 90).toFixed(6);
    const lon = (Math.random() * 360 - 180).toFixed(6);
    return { lat: parseFloat(lat), lon: parseFloat(lon) };
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
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;

    if (!serviceDescription || !bidPrice || !latitude || !longitude || !startTime || !endTime) {
        alert("Please fill in all fields");
        return;
    }

    const bidData = {
        service: serviceDescription,
        price: parseFloat(bidPrice),
        lat: parseFloat(latitude),
        lon: parseFloat(longitude),
        start_time: Math.floor(new Date(startTime).getTime() / 1000),
        end_time: Math.floor(new Date(endTime).getTime() / 1000)
    };

    makeApiRequest('/make_bid', 'POST', bidData);
}

function loginHandler() {
    if (authToken) {
        authToken = null;
        updateUI();
    } else {
        const username = prompt("Enter your username:");
        const password = prompt("Enter your password:");
        if (username && password) {
            makeApiRequest('/login', 'POST', { username, password });
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const addLocationButton = document.getElementById('add-location');
    if (addLocationButton) {
        addLocationButton.addEventListener('click', addLocationHandler);
    }

    const submitBidButton = document.getElementById('submit-bid');
    if (submitBidButton) {
        submitBidButton.addEventListener('click', submitBidHandler);
    }

    const loginButton = document.getElementById('login-btn');
    if (loginButton) {
        loginButton.addEventListener('click', loginHandler);
    }

    updateUI();
});