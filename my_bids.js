// Constants 
const API_BASE_URL = window.location.protocol === 'https:' ? 
  'https://rse-api.com:5002' : 'http://100.26.236.1:5001';
const API_TIMEOUT = 5000; // 5 second timeout

// Authentication token
let authToken = '';
let currentUsername = '';
let currentBidId = null; // For tracking which bid is currently being viewed

// DOM Elements
const elements = {
  // Auth elements
  loginSection: document.getElementById('login-section'),
  userInfo: document.getElementById('user-info'),
  loginBtn: document.getElementById('login-btn'),
  logoutBtn: document.getElementById('logout-btn'),
  username: document.getElementById('username'),
  password: document.getElementById('password'),
  loginMessage: document.getElementById('login-message'),
  profileUsername: document.getElementById('profile-username'),
  
  // Bids section
  bidsSection: document.getElementById('bids-section'),
  bidsList: document.getElementById('bids-list'),
  bidsLoading: document.getElementById('bids-loading'),
  noBidsMessage: document.getElementById('no-bids-message'),
  refreshBidsBtn: document.getElementById('refresh-bids-btn'),
  statusFilter: document.getElementById('status-filter'),
  applyFilterBtn: document.getElementById('apply-filter-btn'),
  
  // Bid form elements
  newBidBtn: document.getElementById('new-bid-btn'),
  bidFormContainer: document.getElementById('bid-form-container'),
  closeFormBtn: document.getElementById('close-form-btn'),
  bidForm: document.getElementById('bid-form'),
  serviceDescription: document.getElementById('service-description'),
  bidLatitude: document.getElementById('bid-latitude'),
  bidLongitude: document.getElementById('bid-longitude'),
  updateLocationBtn: document.getElementById('update-location-btn'),
  bidPrice: document.getElementById('bid-price'),
  bidEndDate: document.getElementById('bid-end-date'),
  bidEndTime: document.getElementById('bid-end-time'),
  submitBidBtn: document.getElementById('submit-bid-btn'),
  bidSubmitMessage: document.getElementById('bid-submit-message'),
  
  // Modal elements
  bidDetailsModal: document.getElementById('bid-details-modal'),
  bidDetailsContent: document.getElementById('bid-details-content'),
  closeDetailsBtn: document.getElementById('close-details-btn'),
  closeModalBtn: document.getElementById('close-modal-btn'),
  cancelBidBtn: document.getElementById('cancel-bid-btn')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  // Set up event listeners
  setupEventListeners();
  
  // Check for saved auth token
  checkAuthStatus();
  
  // Set default bid expiry time (24 hours from now)
  setDefaultBidExpiryTime();
});

// Set up event listeners
function setupEventListeners() {
  // Auth listeners
  if (elements.loginBtn) {
    elements.loginBtn.addEventListener('click', handleLogin);
  }
  
  if (elements.logoutBtn) {
    elements.logoutBtn.addEventListener('click', handleLogout);
  }
  
  // Bids section listeners
  if (elements.refreshBidsBtn) {
    elements.refreshBidsBtn.addEventListener('click', fetchUserBids);
  }
  
  if (elements.applyFilterBtn) {
    elements.applyFilterBtn.addEventListener('click', applyBidFilter);
  }
  
  if (elements.newBidBtn) {
    elements.newBidBtn.addEventListener('click', showBidForm);
  }
  
  // Bid form listeners
  if (elements.closeFormBtn) {
    elements.closeFormBtn.addEventListener('click', hideBidForm);
  }
  
  if (elements.updateLocationBtn) {
    elements.updateLocationBtn.addEventListener('click', updateBidLocation);
  }
  
  if (elements.bidForm) {
    elements.bidForm.addEventListener('submit', handleBidSubmit);
  }
  
  // Modal listeners
  if (elements.closeDetailsBtn) {
    elements.closeDetailsBtn.addEventListener('click', hideBidDetailsModal);
  }
  
  if (elements.closeModalBtn) {
    elements.closeModalBtn.addEventListener('click', hideBidDetailsModal);
  }
  
  if (elements.cancelBidBtn) {
    elements.cancelBidBtn.addEventListener('click', handleCancelBid);
  }
}

// Set default bid expiry time
function setDefaultBidExpiryTime() {
  if (elements.bidEndDate && elements.bidEndTime) {
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
    elements.bidEndTime.value = formattedTime;
  }
}

// Check for saved auth token
function checkAuthStatus() {
  const savedToken = localStorage.getItem('rseAuthToken');
  const savedUsername = localStorage.getItem('rseUsername');
  
  if (savedToken && savedUsername) {
    authToken = savedToken;
    currentUsername = savedUsername;
    showAuthenticatedUI();
    fetchUserBids();
  }
}

// Authentication handlers
async function handleLogin() {
  const username = elements.username.value.trim();
  const password = elements.password.value;
  
  if (!username || !password) {
    showLoginMessage("Please enter both username and password", "error");
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
        username,
        password
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
    fetchUserBids();
    
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
  
  // Show login UI
  showLoginUI();
}

// UI State Functions
function showAuthenticatedUI() {
  if (elements.loginSection) elements.loginSection.style.display = 'none';
  if (elements.userInfo) {
    elements.userInfo.style.display = 'block';
    if (elements.profileUsername) {
      elements.profileUsername.textContent = `Logged in as: ${currentUsername}`;
    }
  }
  if (elements.bidsSection) elements.bidsSection.style.display = 'block';
}

function showLoginUI() {
  if (elements.loginSection) elements.loginSection.style.display = 'block';
  if (elements.userInfo) elements.userInfo.style.display = 'none';
  if (elements.bidsSection) elements.bidsSection.style.display = 'none';
  if (elements.bidFormContainer) elements.bidFormContainer.style.display = 'none';
  
  // Clear login form
  if (elements.username) elements.username.value = '';
  if (elements.password) elements.password.value = '';
}

function showLoginMessage(message, type) {
  if (!elements.loginMessage) return;
  
  elements.loginMessage.textContent = message;
  elements.loginMessage.className = '';
  elements.loginMessage.classList.add(`message-${type}`);
  elements.loginMessage.style.display = 'block';
  
  // Hide success message after 5 seconds
  if (type === "success") {
    setTimeout(() => {
      elements.loginMessage.style.display = 'none';
    }, 5000);
  }
}

// Bid form functions
function showBidForm() {
  if (elements.bidFormContainer) {
    elements.bidFormContainer.style.display = 'block';
    
    // Update location if possible
    if (navigator.geolocation) {
      updateBidLocation();
    }
    
    elements.bidFormContainer.scrollIntoView({ behavior: 'smooth' });
  }
}

function hideBidForm() {
  if (elements.bidFormContainer) {
    elements.bidFormContainer.style.display = 'none';
  }
}

function updateBidLocation() {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        
        if (elements.bidLatitude && elements.bidLongitude) {
          elements.bidLatitude.value = lat.toFixed(6);
          elements.bidLongitude.value = lon.toFixed(6);
        }
        
        showBidSubmitMessage("Location updated successfully", "success");
      },
      (error) => {
        showBidSubmitMessage(`Geolocation error: ${error.message}`, "error");
      }
    );
  } else {
    showBidSubmitMessage("Geolocation is not supported by this browser", "error");
  }
}

function showBidSubmitMessage(message, type) {
  if (!elements.bidSubmitMessage) return;
  
  elements.bidSubmitMessage.textContent = message;
  elements.bidSubmitMessage.className = '';
  elements.bidSubmitMessage.classList.add(`message-${type}`);
  elements.bidSubmitMessage.style.display = 'block';
  
  // Hide success message after 5 seconds
  if (type === "success") {
    setTimeout(() => {
      elements.bidSubmitMessage.style.display = 'none';
    }, 5000);
  }
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
  const description = service; // Use service as description
  const lat = parseFloat(elements.bidLatitude.value);
  const lon = parseFloat(elements.bidLongitude.value);
  const price = parseFloat(elements.bidPrice.value);
  
  // Handle date and time inputs
  const dateValue = elements.bidEndDate.value;
  const timeValue = elements.bidEndTime.value;
  
  // Validate date format
  if (!dateValue.match(/^\d{4}-\d{2}-\d{2}$/)) {
    showBidSubmitMessage("Please enter date in YYYY-MM-DD format", "error");
    return;
  }
  
  // Validate time format
  if (!timeValue.match(/^\d{2}:\d{2}$/)) {
    showBidSubmitMessage("Please enter time in HH:MM format", "error");
    return;
  }
  
  // Create date object from inputs
  const endTimeDate = new Date(`${dateValue}T${timeValue}`);
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
        description,
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
    
    // Clear form
    elements.serviceDescription.value = '';
    elements.bidPrice.value = '';
    
    // Refresh bids list
    fetchUserBids();
    
    // Hide form after successful submission
    setTimeout(() => {
      hideBidForm();
    }, 2000);
    
  } catch (error) {
    showBidSubmitMessage(`Error: ${error.message}`, "error");
  }
}

// Fetch user bids
async function fetchUserBids() {
  if (!authToken) {
    return;
  }
  
  // Show loading indicator
  if (elements.bidsLoading) elements.bidsLoading.style.display = 'block';
  if (elements.bidsList) elements.bidsList.innerHTML = '';
  if (elements.noBidsMessage) elements.noBidsMessage.style.display = 'none';
  
  try {
    const response = await fetch(`${API_BASE_URL}/account`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch account data');
    }
    
    const data = await response.json();
    
    // Hide loading indicator
    if (elements.bidsLoading) elements.bidsLoading.style.display = 'none';
    
    // Display bids
    displayBids(data.bids || []);
    
  } catch (error) {
    if (elements.bidsLoading) elements.bidsLoading.style.display = 'none';
    console.error('Error fetching bids:', error);
  }
}

// Display bids
function displayBids(bids) {
  if (!elements.bidsList) return;
  
  // Clear existing bids
  elements.bidsList.innerHTML = '';
  
  // Get selected status filter
  const statusFilter = elements.statusFilter ? elements.statusFilter.value : 'all';
  
  // Filter bids by status if needed
  const filteredBids = statusFilter === 'all' 
    ? bids 
    : bids.filter(bid => bid.status === statusFilter);
  
  if (filteredBids.length === 0) {
    // Show no bids message
    if (elements.noBidsMessage) {
      elements.noBidsMessage.style.display = 'block';
      elements.noBidsMessage.textContent = statusFilter === 'all' 
        ? 'You don\'t have any bids yet.' 
        : `You don't have any ${statusFilter} bids.`;
    }
    return;
  }
  
  // Sort bids by timestamp (newest first)
  filteredBids.sort((a, b) => b.timestamp - a.timestamp);
  
  // Create bid items
  filteredBids.forEach(bid => {
    const bidItem = createBidItem(bid);
    elements.bidsList.appendChild(bidItem);
  });
}

// Create a bid item element
function createBidItem(bid) {
  const bidItem = document.createElement('div');
  bidItem.className = 'bid-item';
  bidItem.dataset.bidId = bid.id;
  
  // Format dates
  const createdDate = new Date(bid.timestamp * 1000).toLocaleString();
  const expiresDate = new Date(bid.end_time * 1000).toLocaleString();
  
  // Determine status styling
  const statusClass = `status-${bid.status || 'pending'}`;
  
  bidItem.innerHTML = `
    <div class="bid-header">
      <div class="bid-title">${bid.service || 'Untitled Service'}</div>
      <div class="bid-price">$${parseFloat(bid.price).toFixed(2)}</div>
    </div>
    <div class="bid-info">
      <div>${bid.description || 'No description provided'}</div>
    </div>
    <div class="bid-footer">
      <div>
        <span class="bid-status ${statusClass}">${bid.status || 'pending'}</span>
      </div>
      <div>${createdDate}</div>
    </div>
  `;
  
  // Add click event to view details
  bidItem.addEventListener('click', () => showBidDetailsModal(bid));
  
  return bidItem;
}

// Apply bid filter
function applyBidFilter() {
  fetchUserBids();
}

// Bid details modal
function showBidDetailsModal(bid) {
  if (!elements.bidDetailsModal || !elements.bidDetailsContent) return;
  
  // Store current bid ID for cancel operation
  currentBidId = bid.id;
  
  // Format dates
  const createdDate = new Date(bid.timestamp * 1000).toLocaleString();
  const expiresDate = new Date(bid.end_time * 1000).toLocaleString();
  
  // Create content
  const content = `
    <div class="detail-item">
      <span class="detail-label">Bid ID:</span>
      <span class="detail-value">${bid.id}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Service:</span>
      <span class="detail-value">${bid.service || 'Untitled Service'}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Description:</span>
      <span class="detail-value">${bid.description || 'No description provided'}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Price:</span>
      <span class="detail-value">$${parseFloat(bid.price).toFixed(2)}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Status:</span>
      <span class="detail-value status-${bid.status || 'pending'}">${bid.status || 'pending'}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Location:</span>
      <span class="detail-value">Lat: ${bid.lat}, Lon: ${bid.lon}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Created:</span>
      <span class="detail-value">${createdDate}</span>
    </div>
    <div class="detail-item">
      <span class="detail-label">Expires:</span>
      <span class="detail-value">${expiresDate}</span>
    </div>
  `;
  
  elements.bidDetailsContent.innerHTML = content;
  
  // Show or hide cancel button based on status
  if (bid.status === 'pending') {
    elements.cancelBidBtn.style.display = 'block';
  } else {
    elements.cancelBidBtn.style.display = 'none';
  }
  
  // Show modal
  elements.bidDetailsModal.style.display = 'flex';
}

function hideBidDetailsModal() {
  if (elements.bidDetailsModal) {
    elements.bidDetailsModal.style.display = 'none';
  }
}

// Cancel bid
async function handleCancelBid() {
  if (!authToken || !currentBidId) {
    return;
  }
  
  const confirmCancel = confirm('Are you sure you want to cancel this bid?');
  
  if (!confirmCancel) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/cancel_bid`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        bid_id: currentBidId
      })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error || 'Failed to cancel bid');
    }
    
    // Hide modal
    hideBidDetailsModal();
    
    // Refresh bids
    fetchUserBids();
    
    // Show success message or alert
    alert('Bid cancelled successfully');
    
  } catch (error) {
    console.error('Error cancelling bid:', error);
    alert(`Error: ${error.message}`);
  }
}