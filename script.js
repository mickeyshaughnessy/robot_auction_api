const API_URL = 'http://100.26.236.1:5001';
let authToken = null;

const loginBtn = document.getElementById('login-btn');
const signupBtn = document.getElementById('signup-btn');
const loginModal = document.getElementById('login-modal');
const signupModal = document.getElementById('signup-modal');
const closeLoginModalBtn = document.getElementById('close-login-modal');
const closeSignupModalBtn = document.getElementById('close-signup-modal');
const loginForm = document.getElementById('login-form');
const signupForm = document.getElementById('signup-form');
const bidForm = document.getElementById('bid-form');
const addLocationButton = document.getElementById('add-location');
const responseDiv = document.getElementById('response');
const serviceDescriptionTextarea = document.getElementById('service-description');
const startTimeInput = document.getElementById('start-time');
const endTimeInput = document.getElementById('end-time');

async function pingAPI() {
    const responseDiv = document.getElementById('response')
    try {
        const response = await fetch(`${API_URL}/ping`)
        const data = await response.json()
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`
    } catch (error) {
        responseDiv.innerHTML = `<pre style="color: red;">Error: ${error.message}</pre>`
    }
}

function initializeForm() {
    setDefaultTimes();
    setRandomServiceDescriptionPlaceholder();
}

function setDefaultTimes() {
    const now = new Date();
    const sevenDaysFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

    const formatDateTimeLocal = (date) => {
        const pad = (num) => num.toString().padStart(2, '0');
        const year = date.getFullYear();
        const month = pad(date.getMonth() + 1);
        const day = pad(date.getDate());
        const hours = pad(date.getHours());
        const minutes = pad(date.getMinutes());
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    startTimeInput.value = formatDateTimeLocal(now);
    endTimeInput.value = formatDateTimeLocal(sevenDaysFromNow);
}

function setRandomServiceDescriptionPlaceholder() {
    try {
        const placeholders = JSON.parse(serviceDescriptionTextarea.getAttribute('data-placeholders'));
        if (Array.isArray(placeholders) && placeholders.length > 0) {
            const randomIndex = Math.floor(Math.random() * placeholders.length);
            serviceDescriptionTextarea.setAttribute('placeholder', placeholders[randomIndex]);
        } else {
            serviceDescriptionTextarea.setAttribute('placeholder', 'Describe the service you want...');
        }
    } catch (error) {
        console.error("Error parsing service descriptions:", error);
        serviceDescriptionTextarea.setAttribute('placeholder', 'Describe the service you want...');
    }
}

function showLoginModal() {
    loginModal.style.display = 'block';
}

function hideLoginModal() {
    loginModal.style.display = 'none';
    loginForm.reset();
}

function showSignupModal() {
    signupModal.style.display = 'block';
}

function hideSignupModal() {
    signupModal.style.display = 'none';
    signupForm.reset();
}

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

        if (!response.ok) {
            throw new Error(result.message || 'An error occurred');
        }

        displayResponse(result);

        if (endpoint === '/login') {
            authToken = result.access_token;
            updateUI();
        }

        return result;
    } catch (error) {
        displayResponse({ error: error.message });
        console.error("API Request Error:", error);
    }
}

function displayResponse(data) {
    if (data.error) {
        responseDiv.innerHTML = `<pre style="color: red;">Error: ${sanitizeHTML(data.error)}</pre>`;
    } else {
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
}

function updateUI() {
    if (authToken) {
        loginBtn.textContent = 'Logout';
        signupBtn.style.display = 'none';
        fetchMyBids();
        fetchRecentBids();
    } else {
        loginBtn.textContent = 'Login';
        signupBtn.style.display = 'inline-block';
        document.getElementById('my-bids').innerHTML = '';
        document.getElementById('recent-bids').innerHTML = '';
    }
}

async function fetchMyBids() {
    const result = await makeApiRequest('/my_bids', 'GET');
    if (result && result.bids && result.bids.length > 0) {
        const bidsHtml = result.bids.map(bid => `
            <div class="bid">
                <p><strong>Service:</strong> ${sanitizeHTML(bid.service)}</p>
                <p><strong>Price:</strong> $${bid.price.toFixed(2)}</p>
                <p><strong>Status:</strong> ${sanitizeHTML(bid.status)}</p>
            </div>
        `).join('');
        document.getElementById('my-bids').innerHTML = bidsHtml;
    } else {
        document.getElementById('my-bids').innerHTML = '<p>No bids found.</p>';
    }
}

async function fetchRecentBids() {
    const { lat, lon } = getRandomCoordinates();
    const result = await makeApiRequest('/nearby', 'POST', { lat, lon });
    if (result && result.activities && result.activities.length > 0) {
        const bidsHtml = result.activities.map(bid => `
            <div class="bid">
                <p><strong>Service:</strong> ${sanitizeHTML(bid.service)}</p>
                <p><strong>Location:</strong> (${bid.lat.toFixed(4)}, ${bid.lon.toFixed(4)})</p>
            </div>
        `).join('');
        document.getElementById('recent-bids').innerHTML = bidsHtml;
    } else {
        document.getElementById('recent-bids').innerHTML = '<p>No recent bids nearby.</p>';
    }
}

function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
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
                console.warn("Geolocation error:", error.message);
                const { lat, lon } = getRandomCoordinates();
                document.getElementById('latitude').value = lat;
                document.getElementById('longitude').value = lon;
                alert("Unable to retrieve your location. Using random coordinates.");
            }
        );
    } else {
        console.warn("Geolocation is not supported by this browser.");
        const { lat, lon } = getRandomCoordinates();
        document.getElementById('latitude').value = lat;
        document.getElementById('longitude').value = lon;
        alert("Geolocation is not supported by your browser. Using random coordinates.");
    }
}

function submitBidHandler(event) {
    event.preventDefault();
    const serviceDescription = document.getElementById('service-description').value.trim();
    const bidPrice = parseFloat(document.getElementById('bid-price').value);
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;

    if (!serviceDescription || isNaN(bidPrice) || isNaN(latitude) || isNaN(longitude) || !startTime || !endTime) {
        alert("Please fill in all fields correctly.");
        return;
    }

    const startTimestamp = Math.floor(new Date(startTime).getTime() / 1000);
    const endTimestamp = Math.floor(new Date(endTime).getTime() / 1000);

    if (startTimestamp >= endTimestamp) {
        alert("Start time must be before end time.");
        return;
    }

    const bidData = {
        service: serviceDescription,
        price: bidPrice,
        lat: latitude,
        lon: longitude,
        start_time: startTimestamp,
        end_time: endTimestamp
    };

    makeApiRequest('/make_bid', 'POST', bidData).then(response => {
        if (response && !response.error) {
            bidForm.reset();
            setDefaultTimes();
            setRandomServiceDescriptionPlaceholder();
            fetchMyBids();
            fetchRecentBids();
            alert("Bid submitted successfully!");
        }
    });
}

function loginHandler() {
    if (authToken) {
        authToken = null;
        updateUI();
        alert("Logged out successfully.");
    } else {
        showLoginModal();
    }
}