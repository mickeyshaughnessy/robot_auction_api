const API_URL = 'https://100.26.236.1:5001'; // Ensure this uses HTTPS
let authToken = null;

// DOM Elements
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

// Show Login Modal
function showLoginModal() {
    loginModal.style.display = 'block';
}

// Hide Login Modal
function hideLoginModal() {
    loginModal.style.display = 'none';
    loginForm.reset();
}

// Show Sign-Up Modal
function showSignupModal() {
    signupModal.style.display = 'block';
}

// Hide Sign-Up Modal
function hideSignupModal() {
    signupModal.style.display = 'none';
    signupForm.reset();
}

// Make API Request
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

// Display API Response
function displayResponse(data) {
    if (data.error) {
        responseDiv.innerHTML = `<pre style="color: red;">Error: ${sanitizeHTML(data.error)}</pre>`;
    } else {
        responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    }
}

// Update UI Based on Authentication
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

// Fetch User's Bids
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

// Fetch Recent Nearby Bids
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

// Sanitize HTML to prevent XSS
function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

// Generate Random Coordinates (Fallback)
function getRandomCoordinates() {
    const lat = (Math.random() * 180 - 90).toFixed(6);
    const lon = (Math.random() * 360 - 180).toFixed(6);
    return { lat: parseFloat(lat), lon: parseFloat(lon) };
}

// Handle Location Addition
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

// Handle Bid Submission
function submitBidHandler(event) {
    event.preventDefault();
    const serviceDescription = document.getElementById('service-description').value.trim();
    const bidPrice = parseFloat(document.getElementById('bid-price').value);
    const latitude = parseFloat(document.getElementById('latitude').value);
    const longitude = parseFloat(document.getElementById('longitude').value);
    const startTime = document.getElementById('start-time').value;
    const endTime = document.getElementById('end-time').value;

    // Basic Validation
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
            fetchMyBids();
            fetchRecentBids();
            alert("Bid submitted successfully!");
        }
    });
}

// Handle Login/Logout
function loginHandler() {
    if (authToken) {
        // Logout
        authToken = null;
        updateUI();
        alert("Logged out successfully.");
    } else {
        // Show Login Modal
        showLoginModal();
    }
}

// Handle Sign-Up Button Click
function signupHandler() {
    showSignupModal();
}

// Handle Login Form Submission
loginForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const username = loginForm.username.value.trim();
    const password = loginForm.password.value.trim();

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    makeApiRequest('/login', 'POST', { username, password }).then(response => {
        if (response && !response.error) {
            hideLoginModal();
            alert("Logged in successfully.");
        }
    });
});

// Handle Sign-Up Form Submission
signupForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const username = signupForm['signup-username'].value.trim();
    const email = signupForm['signup-email'].value.trim();
    const password = signupForm['signup-password'].value.trim();
    const confirmPassword = signupForm['signup-confirm-password'].value.trim();

    // Basic Validation
    if (!username || !email || !password || !confirmPassword) {
        alert("Please fill in all fields.");
        return;
    }

    if (password !== confirmPassword) {
        alert("Passwords do not match.");
        return;
    }

    // Password Strength Validation (optional)
    if (password.length < 6) {
        alert("Password must be at least 6 characters long.");
        return;
    }

    const signupData = {
        username,
        email,
        password
    };

    makeApiRequest('/signup', 'POST', signupData).then(response => {
        if (response && !response.error) {
            hideSignupModal();
            alert("Account created successfully. You can now log in.");
        }
    });
});

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    addLocationButton.addEventListener('click', addLocationHandler);
    bidForm.addEventListener('submit', submitBidHandler);
    loginBtn.addEventListener('click', loginHandler);
    signupBtn.addEventListener('click', signupHandler);
    closeLoginModalBtn.addEventListener('click', hideLoginModal);
    closeSignupModalBtn.addEventListener('click', hideSignupModal);
    window.addEventListener('click', (event) => {
        if (event.target === loginModal) {
            hideLoginModal();
        }
        if (event.target === signupModal) {
            hideSignupModal();
        }
    });

    updateUI();
});
