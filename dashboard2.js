// Constants and Configuration
const API_BASE_URL = window.location.protocol === 'https:' ? 
  'https://rse-api.com:5002' : 'http://100.26.236.1:5001';
const API_TIMEOUT = 5000;
const NEARBY_POLL_INTERVAL = 5000; // 5 seconds
let pollingInterval = null;

// Authentication state
let authToken = '';
let currentUsername = '';

// Map related variables
let map;
let markers = {
  bids: new Map(),
  completedJobs: new Map()
};

  // DOM Elements
const elements = {
  // Dashboard elements
  map: document.getElementById('map'),
  activityLog: document.getElementById('activity-log'),
  submitBidBtn: document.getElementById('submit-bid'),
  showBidsCheckbox: document.getElementById('show-bids'),
  showCompletedJobsCheckbox: document.getElementById('show-completed-jobs'),
  submissionData: document.getElementById('submission-data'),
  
  // Bid form elements
  bidForm: document.getElementById('bid-form'),
  serviceDescription: document.getElementById('service-description'),
  bidLatitude: document.getElementById('bid-latitude'),
  bidLongitude: document.getElementById('bid-longitude'),
  bidPrice: document.getElementById('bid-price'),
  bidEndDate: document.getElementById('bid-end-date'),
  bidEndTimeInput: document.getElementById('bid-end-time-input'),
  updateLocationBtn: document.getElementById('update-location-btn'),
  submitBidBtn2: document.getElementById('submit-bid-btn'),
  bidSubmitMessage: document.getElementById('bid-submit-message'),
  
  // Auth elements to be added
  loginSection: null,
  loginBtn: null,
  loginMessage: null,
  userInfo: null,
  logoutBtn: null
};

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', () => {
  // Initialize the map
  initMap();
  
  // Add auth UI to dashboard
  addAuthInterfaceToDashboard();
  
  // Set up event listeners
  setupEventListeners();
  
  // Check for saved auth token
  checkAuthStatus();
  
  // Setup filter controls
  setupFilterControls();
});

// Initialize map
function initMap(lat = 40.7128, lon = -74.0060) {
  map = L.map('map').setView([lat, lon], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);
  
  // Try to get user's location
  getUserLocation();
}

// Get user's location
function getUserLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLat = position.coords.latitude;
        const userLon = position.coords.longitude;
        map.setView([userLat, userLon], 13);
        
        // Add a marker for user's location
        const userMarker = L.marker([userLat, userLon]).addTo(map)
          .bindPopup("Your Location").openPopup();
        
        // Log user location in activity feed
        logActivity("User location detected", "info");
        
        // Update bid form with location
        updateBidFormLocation(userLat, userLon);
        
        // If authenticated, automatically search nearby
        if (authToken) {
          searchNearbyJobs(userLat, userLon);
        }
      },
      (error) => {
        logActivity(`Geolocation error: ${error.message}`, "error");
      }
    );
  } else {
    logActivity("Geolocation is not supported by this browser.", "error");
  }
}

// Update bid form with location
function updateBidFormLocation(lat, lon) {
  if (elements.bidLatitude && elements.bidLongitude) {
    elements.bidLatitude.value = lat.toFixed(6);
    elements.bidLongitude.value = lon.toFixed(6);
    
    // Ensure they're editable
    elements.bidLatitude.readOnly = false;
    elements.bidLongitude.readOnly = false;
  }
}

// Update bid location
function updateBidLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const userLat = position.coords.latitude;
        const userLon = position.coords.longitude;
        
        // Update bid form with location
        updateBidFormLocation(userLat, userLon);
        
        // Show success message
        showBidSubmitMessage("Location updated successfully", "success");
      },
      (error) => {
        showBidSubmitMessage(`Geolocation error: ${error.message}`, "error");
      }
    );
  } else {
    showBidSubmitMessage("Geolocation is not supported by this browser.", "error");
  }
}

// Add auth interface to dashboard
function addAuthInterfaceToDashboard() {
  // Create login section
  const authContainer = document.createElement('div');
  authContainer.className = 'auth-container';
  authContainer.innerHTML = `
    <div id="loginSection" class="login-section">
      <h3>Login to access nearby services</h3>
      <div class="form-group">
        <label for="username">Username:</label>
        <input type="text" id="username" name="username" required>
      </div>
      <div class="form-group">
        <label for="password">Password:</label>
        <input type="password" id="password" name="password" required>
      </div>
      <button id="loginBtn" type="button">Login</button>
      <div id="loginMessage"></div>
    </div>
    
    <div id="userInfo" class="user-info" style="display: none;">
      <div class="user-profile">
        <span id="profile-username"></span>
        <button id="logoutBtn" type="button">Logout</button>
      </div>
      <div id="nearbySearchControls" class="nearby-controls">
        <button id="searchNearbyBtn" type="button">Search Nearby Jobs</button>
        <div id="nearbyMessage"></div>
      </div>
    </div>
  `;
  
  // Add auth container to the console container
  const consoleContainer = document.querySelector('.console-container');
  if (consoleContainer) {
    consoleContainer.prepend(authContainer);
    
    // Update element references
    elements.loginSection = document.getElementById('loginSection');
    elements.loginBtn = document.getElementById('loginBtn');
    elements.loginMessage = document.getElementById('loginMessage');
    elements.userInfo = document.getElementById('userInfo');
    elements.logoutBtn = document.getElementById('logoutBtn');
    elements.nearbySearchBtn = document.getElementById('searchNearbyBtn');
    elements.nearbyMessage = document.getElementById('nearbyMessage');
  }
}

// Set up event listeners
function setupEventListeners() {
  // Grab job button functionality removed
  
  if (elements.submitBidBtn) {
    elements.submitBidBtn.addEventListener('click', () => {
      // Show bid form
      const bidFormContainer = document.getElementById('bid-form-container');
      if (bidFormContainer) {
        bidFormContainer.scrollIntoView({ behavior: 'smooth' });
      }
    });
  }
  
  // Auth event listeners
  if (elements.loginBtn) {
    elements.loginBtn.addEventListener('click', handleLogin);
  }
  
  if (elements.logoutBtn) {
    elements.logoutBtn.addEventListener('click', handleLogout);
  }
  
  if (elements.nearbySearchBtn) {
    elements.nearbySearchBtn.addEventListener('click', () => {
      const center = map.getCenter();
      searchNearbyJobs(center.lat, center.lng);
    });
  }
  
  // Bid form event listeners
  if (elements.updateLocationBtn) {
    elements.updateLocationBtn.addEventListener('click', updateBidLocation);
  }
  
  if (elements.bidForm) {
    elements.bidForm.addEventListener('submit', handleBidSubmit);
  }
  
  // Set default bid expiry time (24 hours from now)
  if (elements.bidEndDate && elements.bidEndTimeInput) {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Format date as YYYY-MM-DD
    const year = tomorrow.getFullYear();
    const month = String(tomorrow.getMonth() + 1).padStart(2, '0');
    const day = String(tomorrow.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    
    // Format time as HH:MM
    const hours = String(tomorrow.getHours()).padStart(2, '0');
    const minutes = String(tomorrow.getMinutes()).padStart(2, '0');
    const formattedTime = `${hours}:${minutes}`;
    
    elements.bidEndDate.value = formattedDate;
    elements.bidEndTimeInput.value = formattedTime;
  }
}

// Auth related functions
function checkAuthStatus() {
  const savedToken = localStorage.getItem('rseAuthToken');
  const savedUsername = localStorage.getItem('rseUsername');
  
  if (savedToken && savedUsername) {
    authToken = savedToken;
    currentUsername = savedUsername;
    showAuthenticatedUI();
    
    // Start polling for nearby jobs
    startNearbyJobsPolling();
  }
}

async function handleLogin() {
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;
  
  if (!username || !password) {
    showLoginMessage("Please enter both username and password.", "error");
    return;
  }
  
  showLoginMessage("Logging in...", "info");
  
  try {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: username,
        password: password
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }
    
    // Save token and username
    authToken = data.token;
    currentUsername = username;
    localStorage.setItem('rseAuthToken', authToken);
    localStorage.setItem('rseUsername', currentUsername);
    
    showAuthenticatedUI();
    showLoginMessage("Login successful!", "success");
    
    // Start polling for nearby jobs
    startNearbyJobsPolling();
    
  } catch (error) {
    showLoginMessage(`Error: ${error.message}`, "error");
  }
}

function handleLogout() {
  // Clear auth data
  authToken = '';
  currentUsername = '';
  localStorage.removeItem('rseAuthToken');
  localStorage.removeItem('rseUsername');
  
  // Stop polling for nearby jobs
  stopNearbyJobsPolling();
  
  // Clear markers
  clearAllMarkers();
  
  // Show login UI
  showLoginUI();
  
  // Log to activity feed
  logActivity("Logged out successfully", "info");
}

function showAuthenticatedUI() {
  if (elements.loginSection) elements.loginSection.style.display = 'none';
  if (elements.userInfo) {
    elements.userInfo.style.display = 'block';
    const profileUsername = document.getElementById('profile-username');
    if (profileUsername) {
      profileUsername.textContent = `Logged in as: ${currentUsername}`;
    }
  }
  
  // Log to activity feed
  logActivity(`User ${currentUsername} logged in`, "info");
}

function showLoginUI() {
  if (elements.loginSection) elements.loginSection.style.display = 'block';
  if (elements.userInfo) elements.userInfo.style.display = 'none';
  
  // Clear login form
  if (document.getElementById('username')) document.getElementById('username').value = '';
  if (document.getElementById('password')) document.getElementById('password').value = '';
}

function showLoginMessage(message, type) {
  if (!elements.loginMessage) return;
  
  elements.loginMessage.textContent = message;
  elements.loginMessage.className = '';
  elements.loginMessage.classList.add(`message-${type}`);
}

// Nearby jobs polling
function startNearbyJobsPolling() {
  // Clear any existing interval
  if (pollingInterval) {
    clearInterval(pollingInterval);
  }
  
  // Get current map center
  const center = map.getCenter();
  
  // Immediately search for nearby jobs
  searchNearbyJobs(center.lat, center.lng);
  
  // Set up interval for polling
  pollingInterval = setInterval(() => {
    const center = map.getCenter();
    searchNearbyJobs(center.lat, center.lng);
  }, NEARBY_POLL_INTERVAL);
  
  logActivity("Started polling for nearby jobs", "info");
}

function stopNearbyJobsPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
    logActivity("Stopped polling for nearby jobs", "info");
  }
}

// Search for nearby jobs
async function searchNearbyJobs(lat, lon) {
  if (!authToken) {
    logActivity("Authentication required to search for nearby jobs", "error");
    return;
  }
  
  try {
    showNearbyMessage("Searching for nearby jobs...", "info");
    
    const response = await fetch(`${API_BASE_URL}/nearby`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        lat: parseFloat(lat),
        lon: parseFloat(lon)
      })
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to fetch nearby jobs');
    }
    
    const data = await response.json();
    
    if (data.error) {
      throw new Error(data.error);
    }
    
    displayNearbyJobs(data.bids || {});
    
  } catch (error) {
    showNearbyMessage(`Error: ${error.message}`, "error");
    logActivity(`Error fetching nearby jobs: ${error.message}`, "error");
  }
}

function displayNearbyJobs(bids) {
  const bidCount = Object.keys(bids).length;
  showNearbyMessage(`Found ${bidCount} service${bidCount !== 1 ? 's' : ''} nearby!`, "success");
  
  // Clear existing bid markers before adding new ones
  clearMarkers('bids');
  
  // Add markers for each bid
  for (const [bidId, bid] of Object.entries(bids)) {
    const marker = createBidMarker(bidId, bid);
    markers.bids.set(bidId, marker);
  }
  
  // Update visibility based on filter state
  updateMarkersVisibility();
  
  // Also update the info in the activity log
  if (bidCount > 0) {
    logActivity(`Found ${bidCount} nearby job${bidCount !== 1 ? 's' : ''}`, "info");
  } else {
    logActivity("No nearby jobs found", "info");
  }
}

function createBidMarker(bidId, bid) {
  // Create a custom icon for bids
  const bidIcon = L.divIcon({
    className: 'custom-bid-icon',
    html: `<div style="background-color:blue; width:12px; height:12px; border-radius:50%; border:2px solid white;"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6]
  });
  
  // Create the marker and add it to the map
  const marker = L.marker([bid.lat, bid.lon], { icon: bidIcon }).addTo(map);
  
  // Create popup content - grab job button removed
  const popupContent = `
    <div class="bid-popup">
      <h3>${bid.title || 'Untitled Service'}</h3>
      <p><strong>Posted by:</strong> ${bid.username || 'Unknown user'}</p>
      <p><strong>Price:</strong> ${bid.price || 'Not specified'}</p>
      <p><strong>Description:</strong> ${bid.description || 'No description provided'}</p>
    </div>
  `;
  
  // Bind popup to marker
  marker.bindPopup(popupContent);
  
  return marker;
}

// grabJob functionality has been removed

// Won job marker functionality has been removed

// Grab job button handler removed

// Marker management functions
function clearMarkers(type) {
  if (markers[type]) {
    for (const marker of markers[type].values()) {
      map.removeLayer(marker);
    }
    markers[type].clear();
  }
}

function clearAllMarkers() {
  clearMarkers('bids');
  clearMarkers('completedJobs');
}

// Filter controls
function setupFilterControls() {
  if (elements.showBidsCheckbox) {
    elements.showBidsCheckbox.addEventListener('change', updateMarkersVisibility);
  }
  
  // Won jobs checkbox event listener removed
  
  if (elements.showCompletedJobsCheckbox) {
    elements.showCompletedJobsCheckbox.addEventListener('change', updateMarkersVisibility);
  }
}

function updateMarkersVisibility() {
  // Update bids visibility
  const showBids = elements.showBidsCheckbox ? elements.showBidsCheckbox.checked : true;
  for (const marker of markers.bids.values()) {
    if (showBids) {
      if (!map.hasLayer(marker)) map.addLayer(marker);
    } else {
      if (map.hasLayer(marker)) map.removeLayer(marker);
    }
  }
  
  // Won jobs visibility control removed
  
  // Update completed jobs visibility
  const showCompletedJobs = elements.showCompletedJobsCheckbox ? elements.showCompletedJobsCheckbox.checked : true;
  for (const marker of markers.completedJobs.values()) {
    if (showCompletedJobs) {
      if (!map.hasLayer(marker)) map.addLayer(marker);
    } else {
      if (map.hasLayer(marker)) map.removeLayer(marker);
    }
  }
}

// UI helper functions
function showNearbyMessage(message, type) {
  if (!elements.nearbyMessage) return;
  
  elements.nearbyMessage.textContent = message;
  elements.nearbyMessage.className = '';
  elements.nearbyMessage.classList.add(`message-${type}`);
}

function logActivity(message, type = "info") {
  if (!elements.activityLog) return;
  
  const timestamp = new Date().toLocaleTimeString();
  const logItem = document.createElement('div');
  logItem.className = `log-item log-${type}`;
  logItem.textContent = `[${timestamp}] ${message}`;
  elements.activityLog.appendChild(logItem);
  
  // Scroll to bottom
  elements.activityLog.scrollTop = elements.activityLog.scrollHeight;
  
  // Limit log entries to prevent performance issues
  while (elements.activityLog.children.length > 100) {
    elements.activityLog.removeChild(elements.activityLog.firstChild);
  }
}

// Add CSS styles for new UI elements
function addStyles() {
  const style = document.createElement('style');
  style.textContent = `
    .auth-container {
      margin-bottom: 15px;
      padding: 10px;
      background-color: #f8f9fa;
      border-radius: 8px;
    }
    
    .login-section, .user-info {
      padding: 10px;
    }
    
    .form-group {
      margin-bottom: 10px;
    }
    
    .form-group label {
      display: block;
      margin-bottom: 5px;
      font-weight: bold;
    }
    
    .form-group input {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    
    button {
      background-color: #4285f4;
      color: white;
      border: none;
      padding: 8px 12px;
      border-radius: 4px;
      cursor: pointer;
      margin-right: 5px;
      margin-bottom: 5px;
    }
    
    button:hover {
      background-color: #3367d6;
    }
    
    .nearby-controls {
      margin-top: 10px;
    }
    
    .message-error {
      color: #d32f2f;
      margin: 5px 0;
    }
    
    .message-success {
      color: #388e3c;
      margin: 5px 0;
    }
    
    .message-info {
      color: #1976d2;
      margin: 5px 0;
    }
    
    .message-warning {
      color: #f57c00;
      margin: 5px 0;
    }
    
    .log-item {
      margin: 2px 0;
      padding: 3px;
      font-family: monospace;
    }
    
    .log-error {
      color: #d32f2f;
    }
    
    .log-success {
      color: #388e3c;
    }
    
    .log-info {
      color: #1976d2;
    }
    
    .log-warning {
      color: #f57c00;
    }
    
    .user-profile {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .bid-popup h3 {
      margin-top: 0;
      margin-bottom: 5px;
    }
    
    .bid-popup p {
      margin: 5px 0;
    }
    
    .grab-job-btn {
      margin-top: 10px;
    }
  `;
  
  document.head.appendChild(style);
}

// Handle bid submission
async function handleBidSubmit(e) {
  e.preventDefault();
  
  if (!authToken) {
    showBidSubmitMessage("You must be logged in to submit a bid", "error");
    return;
  }
  
  // Get form values
  const service = elements.serviceDescription.value.trim();
  const lat = parseFloat(elements.bidLatitude.value);
  const lon = parseFloat(elements.bidLongitude.value);
  const price = parseFloat(elements.bidPrice.value);
  const endTimeDate = new Date(elements.bidEndTime.value);
  const endTime = Math.floor(endTimeDate.getTime() / 1000); // Convert to Unix timestamp
  
  // Validate values
  if (!service) {
    showBidSubmitMessage("Please enter a service description", "error");
    return;
  }
  
  if (isNaN(lat) || isNaN(lon)) {
    showBidSubmitMessage("Please provide valid location coordinates", "error");
    return;
  }
  
  if (isNaN(price) || price <= 0) {
    showBidSubmitMessage("Please enter a valid price greater than 0", "error");
    return;
  }
  
  if (isNaN(endTime) || endTime <= Math.floor(Date.now() / 1000)) {
    showBidSubmitMessage("Please enter a valid future end time", "error");
    return;
  }
  
  // Show loading message
  showBidSubmitMessage("Submitting bid...", "info");
  
  try {
    const response = await fetch(`${API_BASE_URL}/submit_bid`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        service,
        lat,
        lon,
        price,
        end_time: endTime
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to submit bid');
    }
    
    // Show success message
    showBidSubmitMessage(`Bid submitted successfully! Bid ID: ${data.bid_id}`, "success");
    
    // Log to activity feed
    logActivity(`Bid submitted: ${service} at ${price}`, "success");
    
    // Clear form
    elements.serviceDescription.value = '';
    elements.bidPrice.value = '';
    
    // Refresh nearby jobs
    const center = map.getCenter();
    searchNearbyJobs(center.lat, center.lng);
    
  } catch (error) {
    showBidSubmitMessage(`Error: ${error.message}`, "error");
    logActivity(`Error submitting bid: ${error.message}`, "error");
  }
}

// Show bid submit message
function showBidSubmitMessage(message, type) {
  if (!elements.bidSubmitMessage) return;
  
  elements.bidSubmitMessage.textContent = message;
  elements.bidSubmitMessage.className = '';
  elements.bidSubmitMessage.classList.add(type);
  
  // Hide success message after 5 seconds
  if (type === "success") {
    setTimeout(() => {
      elements.bidSubmitMessage.className = '';
      elements.bidSubmitMessage.textContent = '';
    }, 5000);
  }
}

// Add styles when the DOM is loaded
document.addEventListener('DOMContentLoaded', addStyles);