/**
 * 🤖 API Documentation Interactive Features
 * Handles try-it forms, API testing, and response display
 */

// API Configuration
const API_CONFIG = {
    baseUrl: 'https://rse-api.com:5002',
    timeout: 10000
};

/**
 * 🔧 Utility Functions
 */

// Get auth token from localStorage or auth.js if available
function getAuthToken() {
    try {
        return localStorage.getItem('auth_token') || 
               (window.AuthManager && window.AuthManager.getToken()) || 
               null;
    } catch (e) {
        return null;
    }
}

// Format JSON response for display
function formatResponse(response, status) {
    const timestamp = new Date().toLocaleTimeString();
    const statusClass = status >= 200 && status < 300 ? 'success' : 'error';
    
    return `
        <div class="api-response-item ${statusClass}">
            <div class="response-header">
                <span class="status-code">${status}</span>
                <span class="timestamp">${timestamp}</span>
            </div>
            <pre class="response-body">${JSON.stringify(response, null, 2)}</pre>
        </div>
    `;
}

// Display response in target element
function displayResponse(targetId, content) {
    const target = document.getElementById(targetId);
    if (target) {
        target.innerHTML = content;
        target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Show loading state
function showLoading(targetId) {
    displayResponse(targetId, `
        <div class="api-response-item loading">
            <div class="loading-spinner"></div>
            <span>Making API request...</span>
        </div>
    `);
}

/**
 * 🌐 API Request Functions
 */

// Generic API request wrapper
async function makeApiRequest(endpoint, options = {}) {
    const url = `${API_CONFIG.baseUrl}${endpoint}`;
    const token = getAuthToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        },
        timeout: API_CONFIG.timeout
    };
    
    const requestOptions = { ...defaultOptions, ...options };
    
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);
        
        const response = await fetch(url, {
            ...requestOptions,
            signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        let responseData;
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            responseData = await response.json();
        } else {
            responseData = { message: await response.text() };
        }
        
        return {
            data: responseData,
            status: response.status,
            ok: response.ok
        };
        
    } catch (error) {
        console.error('API Request Error:', error);
        
        if (error.name === 'AbortError') {
            return {
                data: { error: 'Request timeout' },
                status: 408,
                ok: false
            };
        }
        
        return {
            data: { error: error.message || 'Network error' },
            status: 0,
            ok: false
        };
    }
}

/**
 * 🧪 Try-It Form Functions
 */

// Toggle try-it form visibility
function toggleTryIt(formId) {
    const form = document.getElementById(formId);
    if (form) {
        const isVisible = form.style.display !== 'none';
        form.style.display = isVisible ? 'none' : 'block';
        
        // Clear previous responses when opening
        if (!isVisible) {
            const responseDiv = form.querySelector('.try-it-response');
            if (responseDiv) {
                responseDiv.innerHTML = '';
            }
        }
    }
}

// Register endpoint try-it
async function tryRegister() {
    const username = document.getElementById('try-register-username')?.value;
    const password = document.getElementById('try-register-password')?.value;
    const responseDiv = document.querySelector('#register-try .try-it-response');
    
    if (!username || !password) {
        responseDiv.innerHTML = formatResponse(
            { error: 'Username and password are required' }, 
            400
        );
        return;
    }
    
    if (username.length < 3 || username.length > 20) {
        responseDiv.innerHTML = formatResponse(
            { error: 'Username must be 3-20 characters' }, 
            400
        );
        return;
    }
    
    if (password.length < 8) {
        responseDiv.innerHTML = formatResponse(
            { error: 'Password must be at least 8 characters' }, 
            400
        );
        return;
    }
    
    showLoading('register-try');
    
    const result = await makeApiRequest('/register', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    
    responseDiv.innerHTML = formatResponse(result.data, result.status);
}

// Login endpoint try-it
async function tryLogin() {
    const username = document.getElementById('try-login-username')?.value;
    const password = document.getElementById('try-login-password')?.value;
    const responseDiv = document.querySelector('#login-try .try-it-response');
    
    if (!username || !password) {
        responseDiv.innerHTML = formatResponse(
            { error: 'Username and password are required' }, 
            400
        );
        return;
    }
    
    showLoading('login-try');
    
    const result = await makeApiRequest('/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    });
    
    responseDiv.innerHTML = formatResponse(result.data, result.status);
    
    // Store token if login successful
    if (result.ok && result.data.access_token) {
        try {
            localStorage.setItem('auth_token', result.data.access_token);
            // Trigger auth state update if AuthManager exists
            if (window.AuthManager && window.AuthManager.updateAuthState) {
                window.AuthManager.updateAuthState();
            }
        } catch (e) {
            console.warn('Could not store auth token:', e);
        }
    }
}

// Submit bid try-it
async function trySubmitBid() {
    const service = document.getElementById('try-bid-service')?.value;
    const lat = parseFloat(document.getElementById('try-bid-lat')?.value);
    const lon = parseFloat(document.getElementById('try-bid-lon')?.value);
    const price = parseFloat(document.getElementById('try-bid-price')?.value);
    const hours = parseInt(document.getElementById('try-bid-hours')?.value) || 24;
    const responseDiv = document.querySelector('#submit-bid-try .try-it-response');
    
    if (!service || isNaN(lat) || isNaN(lon) || isNaN(price)) {
        responseDiv.innerHTML = formatResponse(
            { error: 'All fields are required and coordinates/price must be valid numbers' }, 
            400
        );
        return;
    }
    
    const end_time = Math.floor(Date.now() / 1000) + (hours * 3600);
    
    showLoading('submit-bid-try');
    
    const result = await makeApiRequest('/submit_bid', {
        method: 'POST',
        body: JSON.stringify({
            service,
            lat,
            lon,
            price,
            end_time
        })
    });
    
    responseDiv.innerHTML = formatResponse(result.data, result.status);
}

// Nearby activity try-it
async function tryNearby() {
    const lat = parseFloat(document.getElementById('try-nearby-lat')?.value);
    const lon = parseFloat(document.getElementById('try-nearby-lon')?.value);
    const responseDiv = document.querySelector('#nearby-try .try-it-response');
    
    if (isNaN(lat) || isNaN(lon)) {
        responseDiv.innerHTML = formatResponse(
            { error: 'Valid latitude and longitude are required' }, 
            400
        );
        return;
    }
    
    showLoading('nearby-try');
    
    const result = await makeApiRequest('/nearby', {
        method: 'POST',
        body: JSON.stringify({ lat, lon })
    });
    
    responseDiv.innerHTML = formatResponse(result.data, result.status);
}

/**
 * 🔍 API Status Check Functions
 */

// Check API status
async function checkApiStatus(targetId = 'api-status-response') {
    showLoading(targetId);
    
    const result = await makeApiRequest('/ping', {
        method: 'GET'
    });
    
    displayResponse(targetId, formatResponse(result.data, result.status));
}

// Test ping endpoint specifically
async function testPingEndpoint() {
    await checkApiStatus('ping-response');
}

/**
 * 🎯 Event Listeners and Initialization
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🤖 API Docs interactive features loaded');
    
    // Add event listeners for API status check buttons
    document.querySelectorAll('[data-action="check-api-status"]').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target') || 'api-status-response';
            checkApiStatus(targetId);
        });
    });
    
    // Add keyboard shortcuts for try-it forms
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.ctrlKey) {
            const activeElement = document.activeElement;
            const tryItForm = activeElement.closest('.try-it-form');
            
            if (tryItForm) {
                const submitButton = tryItForm.querySelector('button[onclick]');
                if (submitButton) {
                    submitButton.click();
                }
            }
        }
    });
    
    // Auto-populate location fields with user's location if available
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(function(position) {
            const lat = position.coords.latitude.toFixed(6);
            const lon = position.coords.longitude.toFixed(6);
            
            // Fill in nearby try-it form
            const nearbyLat = document.getElementById('try-nearby-lat');
            const nearbyLon = document.getElementById('try-nearby-lon');
            if (nearbyLat && !nearbyLat.value) nearbyLat.value = lat;
            if (nearbyLon && !nearbyLon.value) nearbyLon.value = lon;
            
            // Fill in bid try-it form
            const bidLat = document.getElementById('try-bid-lat');
            const bidLon = document.getElementById('try-bid-lon');
            if (bidLat && !bidLat.value) bidLat.value = lat;
            if (bidLon && !bidLon.value) bidLon.value = lon;
        }, function(error) {
            console.log('Geolocation not available:', error.message);
        });
    }
    
    // Add helpful tooltips to coordinate fields
    const coordFields = document.querySelectorAll('input[id*="lat"], input[id*="lon"]');
    coordFields.forEach(field => {
        if (field.id.includes('lat')) {
            field.title = 'Latitude: -90 to 90 (e.g., 40.7128 for NYC)';
            field.placeholder = field.placeholder || '40.7128';
        } else if (field.id.includes('lon')) {
            field.title = 'Longitude: -180 to 180 (e.g., -74.0060 for NYC)';
            field.placeholder = field.placeholder || '-74.0060';
        }
    });
});

// Make functions globally available for onclick handlers
window.toggleTryIt = toggleTryIt;
window.tryRegister = tryRegister;
window.tryLogin = tryLogin;
window.trySubmitBid = trySubmitBid;
window.tryNearby = tryNearby;
window.checkApiStatus = checkApiStatus;
window.testPingEndpoint = testPingEndpoint;

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        toggleTryIt,
        tryRegister,
        tryLogin,
        trySubmitBid,
        tryNearby,
        checkApiStatus,
        testPingEndpoint,
        makeApiRequest
    };
}