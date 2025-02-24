// Constants 
const API_BASE_URL = window.location.protocol === 'https:' ? 
  'https://rse-api.com:5002' : 'http://100.26.236.1:5001';
const API_TIMEOUT = 5000; // 5 second timeout
const LOGIN_ENDPOINT = `${API_BASE_URL}/login`;
const REGISTER_ENDPOINT = `${API_BASE_URL}/register`;
const ACCOUNT_ENDPOINT = `${API_BASE_URL}/account`;
const CANCEL_BID_ENDPOINT = `${API_BASE_URL}/cancel_bid`;
const BULLETIN_ENDPOINT = `${API_BASE_URL}/bulletin`;
const SUBMIT_BID_ENDPOINT = `${API_BASE_URL}/submit_bid`;

// Authentication token
let authToken = null;

// Cache DOM elements for auth UI
const elements = {
  // Login and user profile elements
  loginForm: document.getElementById('login-form'),
  registerForm: document.getElementById('register-form'),
  userProfile: document.getElementById('user-profile'),
  loginMessage: document.getElementById('login-message'),
  registerMessage: document.getElementById('register-message'),
  authStatusIndicator: document.getElementById('auth-status-indicator'),
  userDashboardSection: document.getElementById('user-dashboard-section'),
  
  // Original elements from existing script
  loginBtn: document.getElementById('login-btn'),
  signupBtn: document.getElementById('signup-btn'), 
  loginModal: document.getElementById('login-modal'),
  signupModal: document.getElementById('signup-modal'),
  closeLoginModalBtn: document.getElementById('close-login-modal'),
  closeSignupModalBtn: document.getElementById('close-signup-modal'),
  loginFormOriginal: document.getElementById('login-form-original'),
  signupForm: document.getElementById('signup-form'),
  bidForm: document.getElementById('bid-form'),
  addLocationButton: document.getElementById('add-location'),
  responseDiv: document.getElementById('response'),
  serviceDescriptionTextarea: document.getElementById('service-description'),
  startTimeInput: document.getElementById('start-time'),
  endTimeInput: document.getElementById('end-time'),
  statusSpan: document.getElementById('api-status'),
  
  // New bid submission elements
  bidModal: document.getElementById('bid-modal'),
  bidSubmitForm: document.getElementById('bid-submit-form'),
  bidResponseDiv: document.getElementById('bid-response'),
  submitBidBtn: document.getElementById('submit-bid-btn'),
  useRandomLocationBtn: document.getElementById('use-random-location')
};

// Original script.js functions for form initialization
function initializeForm() {
  if (elements.startTimeInput && elements.endTimeInput) {
    setDefaultTimes();
  }
  
  if (elements.serviceDescriptionTextarea) {
    setRandomServiceDescriptionPlaceholder();
  }
}

function setDefaultTimes() {
  const now = new Date();
  const sevenDaysFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  const formatDateTimeLocal = (date) => {
    return date.toISOString().slice(0, 16);
  };

  if (elements.startTimeInput) {
    elements.startTimeInput.value = formatDateTimeLocal(now);
  }
  
  if (elements.endTimeInput) {
    elements.endTimeInput.value = formatDateTimeLocal(sevenDaysFromNow);
  }
}

function setRandomServiceDescriptionPlaceholder() {
  try {
    if (elements.serviceDescriptionTextarea) {
      const placeholders = JSON.parse(elements.serviceDescriptionTextarea.getAttribute('data-placeholders'));
      if (Array.isArray(placeholders) && placeholders.length > 0) {
        const randomIndex = Math.floor(Math.random() * placeholders.length);
        elements.serviceDescriptionTextarea.setAttribute('placeholder', placeholders[randomIndex]);
      }
    }
  } catch (error) {
    console.error("Error parsing service descriptions:", error);
    if (elements.serviceDescriptionTextarea) {
      elements.serviceDescriptionTextarea.setAttribute('placeholder', 'Describe the service you want...');
    }
  }
}

// Initialize bid form with default values
function initializeBidForm() {
  // Get the start time and end time inputs in the bid modal
  const startTimeInput = document.getElementById('start-time');
  const endTimeInput = document.getElementById('end-time');
  
  if (!startTimeInput || !endTimeInput) {
    return;
  }
  
  // Set default times
  const now = new Date();
  const sevenDaysFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
  
  const formatDateTimeLocal = (date) => {
    return date.toISOString().slice(0, 16);
  };
  
  startTimeInput.value = formatDateTimeLocal(now);
  endTimeInput.value = formatDateTimeLocal(sevenDaysFromNow);
  
  // Set random coordinates initially
  const coords = getRandomCoordinates();
  const latInput = document.getElementById('latitude');
  const lonInput = document.getElementById('longitude');
  
  if (latInput && lonInput) {
    latInput.value = coords.lat;
    lonInput.value = coords.lon;
  }
  
  // Set default price
  const priceInput = document.getElementById('bid-price');
  if (priceInput) {
    priceInput.value = '25.00';
  }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  checkApiStatus();
  initializeForm();
  checkAuthStatus();
  
  // Add bid modal to the page if it doesn't exist
  ensureBidModalExists();
  
  // Call this later after the modal might be added to the DOM
  setTimeout(initializeBidForm, 500);
  
  // Form switching event handlers
  if (document.getElementById('show-register-form')) {
    document.getElementById('show-register-form').addEventListener('click', function(e) {
      e.preventDefault();
      elements.loginForm.style.display = 'none';
      elements.registerForm.style.display = 'block';
    });
  }
  
  if (document.getElementById('show-login-form')) {
    document.getElementById('show-login-form').addEventListener('click', function(e) {
      e.preventDefault();
      elements.registerForm.style.display = 'none';
      elements.loginForm.style.display = 'block';
    });
  }
  
  if (document.getElementById('register-now-btn')) {
    document.getElementById('register-now-btn').addEventListener('click', function() {
      // Open the login/register panel and show register form
      elements.registerForm.style.display = 'block';
      elements.loginForm.style.display = 'none';
      
      // Trigger the collapse to open
      const rightFixedContainer = document.getElementById('Right-Fixed-Container');
      if (rightFixedContainer && !rightFixedContainer.classList.contains('show')) {
        document.querySelector('.User-Icon-Large input').click();
      }
    });
  }
  
  // Login form submission
  if (document.getElementById('login-form-element')) {
    document.getElementById('login-form-element').addEventListener('submit', handleLoginSubmit);
  }
  
  // Register form submission
  if (document.getElementById('register-form-element')) {
    document.getElementById('register-form-element').addEventListener('submit', handleRegisterSubmit);
  }
  
  // Logout functionality
  if (document.getElementById('logout-button')) {
    document.getElementById('logout-button').addEventListener('click', function() {
      // Clear stored credentials
      localStorage.removeItem('rseAuthToken');
      localStorage.removeItem('rseUsername');
      sessionStorage.removeItem('rseAuthToken');
      sessionStorage.removeItem('rseUsername');
      
      // Clear auth token
      authToken = null;
      
      // Update UI for logged out state
      showLoggedOutUI();
      updateUI();
      
      // Show success message
      alert('You have been successfully logged out.');
    });
  }
  
  // Community feature buttons
  if (document.getElementById('open-chat-btn')) {
    document.getElementById('open-chat-btn').addEventListener('click', function() {
      const token = localStorage.getItem('rseAuthToken') || sessionStorage.getItem('rseAuthToken');
      if (token) {
        openChatInterface(token);
      }
    });
  }
  
  if (document.getElementById('open-bulletin-btn')) {
    document.getElementById('open-bulletin-btn').addEventListener('click', function() {
      const token = localStorage.getItem('rseAuthToken') || sessionStorage.getItem('rseAuthToken');
      if (token) {
        openBulletinInterface(token);
      }
    });
  }
  
  // Handle the Create New Bid button click
  const createBidBtns = document.querySelectorAll('a[href="make_bid.html"]');
  if (createBidBtns.length > 0) {
    createBidBtns.forEach(btn => {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        
        // Check if user is logged in
        const token = localStorage.getItem('rseAuthToken') || sessionStorage.getItem('rseAuthToken');
        if (!token) {
          alert('Please log in to create a bid.');
          // Open the login panel
          const rightFixedContainer = document.getElementById('Right-Fixed-Container');
          if (rightFixedContainer && !rightFixedContainer.classList.contains('show')) {
            document.querySelector('.User-Icon-Large input').click();
          }
          return;
        }
        
        // Show the bid modal
        const bidModal = new bootstrap.Modal(document.getElementById('bid-modal'));
        bidModal.show();
      });
    });
  }
  
  // Set up random location button
  if (elements.useRandomLocationBtn) {
    elements.useRandomLocationBtn.addEventListener('click', function() {
      const coords = getRandomCoordinates();
      document.getElementById('latitude').value = coords.lat;
      document.getElementById('longitude').value = coords.lon;
    });
  }
  
  // Set up bid submit button
  if (elements.submitBidBtn) {
    elements.submitBidBtn.addEventListener('click', handleBidSubmit);
  }
  
  // Set up API status check buttons
  setupApiStatusButtons();
});

// Add event listeners for API status check buttons
function setupApiStatusButtons() {
  // Select all buttons with the data-action attribute set to "check-api-status"
  const checkStatusButtons = document.querySelectorAll('[data-action="check-api-status"]');
  
  if (checkStatusButtons.length > 0) {
    checkStatusButtons.forEach(button => {
      button.addEventListener('click', function() {
        // Get the target response div from data-target attribute, or default to 'response'
        const targetId = button.getAttribute('data-target') || 'response';
        const responseDiv = document.getElementById(targetId);
        
        if (responseDiv) {
          responseDiv.innerHTML = '<pre style="color: blue;">Checking API status...</pre>';
          pingAPI(responseDiv);
        } else {
          console.error(`Target response div with id "${targetId}" not found`);
        }
      });
    });
  }
}

// API Status Check function
async function pingAPI(targetDiv = null) {
  // Use provided target div or try to find a response div
  const responseDiv = targetDiv || elements.responseDiv || document.getElementById('response');
  
  if (!responseDiv) {
    console.error('No response div found for API status check');
    return;
  }
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);
    
    const response = await fetch(`${API_BASE_URL}/ping`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    
    const data = await response.json();
    
    // Update status indicator if it exists
    updateStatusIndicator(response.ok ? 'online' : 'degraded');
    
    // Display the response in the target div
    responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    
    return data;
  } catch (error) {
    let errorMessage = '';
    
    if (error.name === 'AbortError') {
      errorMessage = `<pre style="color: orange;">Request timed out after ${API_TIMEOUT/1000} seconds</pre>`;
      updateStatusIndicator('timeout');
    } else if (error.message.includes('Mixed Content') || error.message.includes('NetworkError')) {
      errorMessage = `<pre style="color: orange;">Mixed Content Error: This request was blocked due to content security policy.
Try one of these solutions:
1. Click the shield icon ⛨ in your browser's address bar and allow mixed content
2. Use curl command: curl ${API_BASE_URL.replace('https://', '').replace('http://', '')}/ping
3. Use https instead of http</pre>`;
      updateStatusIndicator('offline');
    } else {
      errorMessage = `<pre style="color: orange;">Error: ${error.message}</pre>`;
      updateStatusIndicator('offline');
    }
    
    responseDiv.innerHTML = errorMessage;
    
    console.error('API Status Check Error:', error);
    return { error: error.message };
  }
}

// Check API status
async function checkApiStatus() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(`${API_BASE_URL}/ping`, {
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    const data = await response.json();
    updateStatusIndicator(response.ok ? 'online' : 'degraded');
    return data;
  } catch (error) {
    if (error.name === 'AbortError') {
      updateStatusIndicator('timeout');
    } else {
      updateStatusIndicator('offline');
      console.error('API Status Check Error:', error);
    }
    return { error: error.message };
  }
}

function updateStatusIndicator(status) {
  if (!elements.statusSpan) return;
  
  const statusMap = {
    online: { text: '🟢 Online', color: '#28a745' },
    degraded: { text: '🟡 Degraded', color: '#ffc107' },
    offline: { text: '🔴 Offline', color: '#dc3545' },
    timeout: { text: '🔴 Timeout', color: '#dc3545' }
  };

  const { text, color } = statusMap[status];
  elements.statusSpan.textContent = text;
  elements.statusSpan.style.color = color;
}

// Authentication functions
function checkAuthStatus() {
  const token = localStorage.getItem('rseAuthToken') || sessionStorage.getItem('rseAuthToken');
  const username = localStorage.getItem('rseUsername') || sessionStorage.getItem('rseUsername');
  
  if (token && username) {
    // Set the auth token
    authToken = token;
    
    // Update UI for authenticated user
    showAuthenticatedUI(username, token);
    
    // Fetch and display user data
    fetchAccountData(token);
  }
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const rememberMe = document.getElementById('rememberMe').checked;
  
  if (!username || !password) {
    showMessage(elements.loginMessage, 'Please enter both username and password', 'error');
    return;
  }
  
  try {
    showMessage(elements.loginMessage, 'Logging in...', 'info');
    
    const result = await makeApiRequest('/login', 'POST', {
      username: username,
      password: password
    });
    
    if (!result || result.error) {
      throw new Error(result?.error || 'Login failed');
    }
    
    // Store auth token
    authToken = result.access_token;
    
    if (rememberMe) {
      localStorage.setItem('rseAuthToken', authToken);
      localStorage.setItem('rseUsername', username);
    } else {
      sessionStorage.setItem('rseAuthToken', authToken);
      sessionStorage.setItem('rseUsername', username);
    }
    
    showMessage(elements.loginMessage, 'Login successful!', 'success');
    
    // Update UI for authenticated user
    showAuthenticatedUI(username, authToken);
    
    // Fetch and display user data
    fetchAccountData(authToken);
    
    // Update the main UI
    updateUI();
    
  } catch (error) {
    showMessage(elements.loginMessage, `Error: ${error.message}`, 'error');
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  
  const username = document.getElementById('register-username').value.trim();
  const password = document.getElementById('register-password').value;
  const confirmPassword = document.getElementById('register-confirm-password').value;
  
  if (!username || !password || !confirmPassword) {
    showMessage(elements.registerMessage, 'Please fill in all fields', 'error');
    return;
  }
  
  if (password !== confirmPassword) {
    showMessage(elements.registerMessage, 'Passwords do not match', 'error');
    return;
  }
  
  if (username.length < 3 || username.length > 20) {
    showMessage(elements.registerMessage, 'Username must be between 3 and 20 characters', 'error');
    return;
  }
  
  if (password.length < 8) {
    showMessage(elements.registerMessage, 'Password must be at least 8 characters', 'error');
    return;
  }
  
  try {
    showMessage(elements.registerMessage, 'Creating account...', 'info');
    
    const result = await makeApiRequest('/register', 'POST', {
      username: username,
      password: password
    });
    
    if (!result || result.error) {
      throw new Error(result?.error || 'Registration failed');
    }
    
    showMessage(elements.registerMessage, 'Registration successful! You can now log in.', 'success');
    
    // Clear registration form
    document.getElementById('register-username').value = '';
    document.getElementById('register-password').value = '';
    document.getElementById('register-confirm-password').value = '';
    
    // Auto-fill login form and switch to it after a delay
    document.getElementById('login-username').value = username;
    setTimeout(() => {
      elements.registerForm.style.display = 'none';
      elements.loginForm.style.display = 'block';
    }, 2000);
    
  } catch (error) {
    showMessage(elements.registerMessage, `Error: ${error.message}`, 'error');
  }
}

// API Request function
async function makeApiRequest(endpoint, method, data = null) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
      },
      ...(data && { body: JSON.stringify(data) })
    });

    clearTimeout(timeoutId);
    
    // Handle no content responses
    if (response.status === 204) {
      return { success: true };
    }
    
    const result = await response.json();

    if (response.status === 401) {
      authToken = null;
      localStorage.removeItem('rseAuthToken');
      sessionStorage.removeItem('rseAuthToken');
      updateUI();
      showLoggedOutUI();
      throw new Error('Session expired. Please login again.');
    }

    if (!response.ok) {
      throw new Error(result.message || result.error || 'An error occurred');
    }

    if (elements.responseDiv) {
      displayResponse(result);
    }

    return result;
  } catch (error) {
    const errorMessage = error.name === 'AbortError' ? 
      'Request timed out' : error.message;
    
    if (elements.responseDiv) {
      displayResponse({ error: errorMessage });
    }
    
    console.error("API Request Error:", error);
    return { error: errorMessage };
  }
}

// Helper function to display response data
function displayResponse(data) {
  if (!elements.responseDiv) return;
  
  if (data.error) {
    elements.responseDiv.innerHTML = `<pre style="color: red;">${data.error}</pre>`;
  } else {
    elements.responseDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
  }
}

// UI helper functions
function showMessage(element, message, type) {
  if (!element) return;
  
  element.textContent = message;
  element.style.display = 'block';
  
  // Reset classes
  element.classList.remove('error-message', 'success-message');
  
  // Add appropriate class
  if (type === 'error') {
    element.classList.add('error-message');
  } else if (type === 'success') {
    element.classList.add('success-message');
  }
  
  // Auto hide after 5 seconds for success messages
  if (type === 'success') {
    setTimeout(() => {
      element.style.display = 'none';
    }, 5000);
  }
}

function showAuthenticatedUI(username, token) {
  // Hide login and register forms, show user profile
  if (elements.loginForm) elements.loginForm.style.display = 'none';
  if (elements.registerForm) elements.registerForm.style.display = 'none';
  if (elements.userProfile) elements.userProfile.style.display = 'block';
  
  // Update profile username
  if (document.getElementById('profile-username')) {
    document.getElementById('profile-username').textContent = username;
  }
  
  // Show authentication indicator
  if (elements.authStatusIndicator) {
    elements.authStatusIndicator.style.display = 'block';
  }
  
  // Show the user dashboard section
  if (elements.userDashboardSection) {
    elements.userDashboardSection.style.display = 'block';
  }
}

function showLoggedOutUI() {
  // Show login form, hide register form and user profile
  if (elements.loginForm) elements.loginForm.style.display = 'block';
  if (elements.registerForm) elements.registerForm.style.display = 'none';
  if (elements.userProfile) elements.userProfile.style.display = 'none';
  
  // Clear form fields
  if (document.getElementById('login-username')) {
    document.getElementById('login-username').value = '';
  }
  
  if (document.getElementById('login-password')) {
    document.getElementById('login-password').value = '';
  }
  
  if (document.getElementById('rememberMe')) {
    document.getElementById('rememberMe').checked = false;
  }
  
  // Hide authentication indicator
  if (elements.authStatusIndicator) {
    elements.authStatusIndicator.style.display = 'none';
  }
  
  // Hide the user dashboard section
  if (elements.userDashboardSection) {
    elements.userDashboardSection.style.display = 'none';
  }
}

// Data fetching functions
async function fetchAccountData(token) {
  try {
    const data = await makeApiRequest('/account', 'GET');
    
    if (data && !data.error) {
      // Update user profile with account data
      const ratingElement = document.getElementById('user-rating');
      const totalRatingsElement = document.getElementById('user-total-ratings');
      
      if (ratingElement && totalRatingsElement) {
        if (data.total_ratings > 0) {
          const avgRating = (data.stars / data.total_ratings).toFixed(1);
          ratingElement.textContent = `${avgRating}/5`;
        } else {
          ratingElement.textContent = 'No ratings yet';
        }
        
        totalRatingsElement.textContent = data.total_ratings;
      }
      
      // Update bids display if bids data is available
      if (data.bids && data.bids.length > 0) {
        updateBidsDisplay(data.bids);
      }
    }
  } catch (error) {
    console.error('Error fetching account data:', error);
  }
}

// Function to update bids display
function updateBidsDisplay(bids) {
  // Update recent bids section
  const recentBidsList = document.getElementById('recent-bids-list');
  
  if (recentBidsList) {
    // Clear existing items
    recentBidsList.innerHTML = '';
    
    if (bids && bids.length > 0) {
      // Add each bid to the list
      bids.slice(0, 5).forEach(bid => {
        const bidItem = document.createElement('div');
        bidItem.classList.add('recent-bid-item');
        
        const serviceType = document.createElement('span');
        serviceType.classList.add('bid-service');
        serviceType.textContent = bid.service;
        
        const price = document.createElement('span');
        price.classList.add('bid-price');
        price.textContent = `$${parseFloat(bid.price).toFixed(2)}`;
        
        const status = document.createElement('span');
        status.classList.add('bid-status');
        status.textContent = bid.status || 'Pending';
        
        // Add appropriate status class
        if (bid.status === 'completed') {
          status.classList.add('status-completed');
        } else if (bid.status === 'matched') {
          status.classList.add('status-in-progress');
        } else if (bid.status === 'cancelled') {
          status.classList.add('status-cancelled');
        } else {
          status.classList.add('status-pending');
        }
        
        bidItem.appendChild(serviceType);
        bidItem.appendChild(price);
        bidItem.appendChild(status);
        
        // Add cancel button for pending bids
        if (bid.status === 'pending') {
          const cancelBtn = document.createElement('button');
          cancelBtn.classList.add('cancel-bid-btn');
          cancelBtn.textContent = 'Cancel';
          cancelBtn.dataset.bidId = bid.id;
          cancelBtn.addEventListener('click', function(e) {
            e.preventDefault();
            cancelBid(bid.id);
          });
          bidItem.appendChild(cancelBtn);
        }
        
        recentBidsList.appendChild(bidItem);
      });
    } else {
      // No bids found
      const noBidsMsg = document.createElement('p');
      noBidsMsg.textContent = 'No recent bids found.';
      recentBidsList.appendChild(noBidsMsg);
    }
  }
  
  // Also update bids in other containers if they exist
  if (document.getElementById('my-bids')) {
    updateBidsContainer('my-bids', { bids });
  }
}

// Function to cancel a bid
async function cancelBid(bidId) {
  try {
    const result = await makeApiRequest('/cancel_bid', 'POST', {
      bid_id: bidId
    });
    
    if (result && !result.error) {
      alert('Bid cancelled successfully');
      // Refresh account data to update bid list
      fetchAccountData();
    } else {
      alert(`Error: ${result.error || 'Failed to cancel bid'}`);
    }
  } catch (error) {
    console.error('Error cancelling bid:', error);
    alert(`Error: ${error.message}`);
  }
}

// Function to get random coordinates (for bid form)
function getRandomCoordinates() {
  const lat = (Math.random() * 180 - 90).toFixed(6);
  const lon = (Math.random() * 360 - 180).toFixed(6);
  return { lat, lon };
}

// Update function expected by other parts of the code
function updateUI() {
  // This would be implemented based on requirements
  console.log('UI updated');
}

// Function to update bids container
function updateBidsContainer(containerId, data) {
  // This would be implemented based on requirements
  console.log(`Updated bids in ${containerId}`);
}

// Function to create a bid modal if it doesn't exist
function ensureBidModalExists() {
  // This would be implemented based on requirements
  console.log('Ensuring bid modal exists');
}

// Function to handle bid submission
function handleBidSubmit(e) {
  // This would be implemented based on requirements
  console.log('Handling bid submission');
}