// Constants 
const API_BASE_URL = window.location.protocol === 'https:' ? 
  'https://100.26.236.1:5001' : 'http://100.26.236.1:5001';
const API_TIMEOUT = 5000; // 5 second timeout
const LOGIN_ENDPOINT = `${API_BASE_URL}/login`;
const REGISTER_ENDPOINT = `${API_BASE_URL}/register`;
const ACCOUNT_DATA_ENDPOINT = `${API_BASE_URL}/account_data`;
const RECENT_BIDS_ENDPOINT = `${API_BASE_URL}/my_bids`;
const BULLETIN_ENDPOINT = `${API_BASE_URL}/bulletin`;

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
  statusSpan: document.getElementById('api-status')
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  checkApiStatus();
  initializeForm();
  checkAuthStatus();
  
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
});

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
  } catch (error) {
    if (error.name === 'AbortError') {
      updateStatusIndicator('timeout');
    } else {
      updateStatusIndicator('offline');
      console.error('API Status Check Error:', error);
    }
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
    
    // Fetch recent bids
    fetchRecentBids(token);
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
    
    // Fetch recent bids
    fetchRecentBids(authToken);
    
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
    const data = await makeApiRequest('/account_data', 'GET');
    
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
    }
  } catch (error) {
    console.error('Error fetching account data:', error);
  }
}

async function fetchRecentBids(token) {
  try {
    const data = await makeApiRequest('/my_bids', 'GET');
    
    // Update recent bids section
    const recentBidsList = document.getElementById('recent-bids-list');
    
    if (recentBidsList) {
      // Clear existing items
      recentBidsList.innerHTML = '';
      
      if (data && data.bids && data.bids.length > 0) {
        // Add each bid to the list
        data.bids.slice(0, 5).forEach(bid => {
          const bidItem = document.createElement('div');
          bidItem.classList.add('recent-bid-item');
          
          const serviceType = document.createElement('span');
          serviceType.classList.add('bid-service');
          serviceType.textContent = bid.service;
          
          const price = document.createElement('span');
          price.classList.add('bid-price');
          price.textContent = `$${bid.price.toFixed(2)}`;
          
          const status = document.createElement('span');
          status.classList.add('bid-status');
          status.textContent = bid.status || 'Pending';
          
          // Add appropriate status class
          if (bid.status === 'Completed') {
            status.classList.add('status-completed');
          } else if (bid.status === 'In Progress') {
            status.classList.add('status-in-progress');
          } else {
            status.classList.add('status-pending');
          }
          
          bidItem.appendChild(serviceType);
          bidItem.appendChild(price);
          bidItem.appendChild(status);
          
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
      updateBidsContainer('my-bids', data);
    }
    
  } catch (error) {
    console.error('Error fetching recent bids:', error);
    
    // Show error message in the recent bids section
    const recentBidsList = document.getElementById('recent-bids-list');
    if (recentBidsList) {
      recentBidsList.innerHTML = '<p class="text-danger">Failed to load recent bids.</p>';
    }
  }
}

function updateBidsContainer(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '';
  
  if (data && data.bids && data.bids.length > 0) {
    const bidsList = document.createElement('ul');
    bidsList.className = 'list-group';
    
    data.bids.forEach(bid => {
      const listItem = document.createElement('li');
      listItem.className = 'list-group-item d-flex justify-content-between align-items-center';
      
      const bidInfo = document.createElement('div');
      bidInfo.innerHTML = `
        <strong>${sanitizeHTML(bid.service)}</strong><br>
        <small>Price: $${bid.price.toFixed(2)}</small>
      `;
      
      const statusBadge = document.createElement('span');
      let badgeClass = 'badge bg-secondary';
      
      if (bid.status === 'Completed') {
        badgeClass = 'badge bg-success';
      } else if (bid.status === 'In Progress') {
        badgeClass = 'badge bg-warning text-dark';
      }
      
      statusBadge.className = badgeClass;
      statusBadge.textContent = bid.status || 'Pending';
      
      listItem.appendChild(bidInfo);
      listItem.appendChild(statusBadge);
      bidsList.appendChild(listItem);
    });
    
    container.appendChild(bidsList);
  } else {
    container.innerHTML = '<p class="text-muted">No bids found.</p>';
  }
}

// Feature interface functions
function openChatInterface(token) {
  // Implementation will depend on how chat interface should be displayed
  // For now, let's navigate to the chat page
  window.location.href = 'chat.html';
}

function openBulletinInterface(token) {
  // Implementation will depend on how bulletin interface should be displayed
  // For now, let's navigate to the bulletin page
  window.location.href = 'bulletin.html';
}

// Original script.js functions
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

// Main UI update
function updateUI() {
  const isLoggedIn = Boolean(authToken);
  
  // Update original UI elements if they exist
  if (elements.loginBtn) {
    elements.loginBtn.textContent = isLoggedIn ? 'Logout' : 'Login';
  }
  
  if (elements.signupBtn) {
    elements.signupBtn.style.display = isLoggedIn ? 'none' : 'inline-block';
  }
  
  // Update the new auth UI elements
  if (isLoggedIn) {
    if (elements.userProfile) elements.userProfile.style.display = 'block';
    if (elements.loginForm) elements.loginForm.style.display = 'none';
    if (elements.registerForm) elements.registerForm.style.display = 'none';
    if (elements.userDashboardSection) elements.userDashboardSection.style.display = 'block';
    if (elements.authStatusIndicator) elements.authStatusIndicator.style.display = 'block';
    
    // Fetch data
    fetchAccountData(authToken);
    fetchRecentBids(authToken);
  } else {
    if (elements.userProfile) elements.userProfile.style.display = 'none';
    if (elements.loginForm) elements.loginForm.style.display = 'block';
    if (elements.registerForm) elements.registerForm.style.display = 'none';
    if (elements.userDashboardSection) elements.userDashboardSection.style.display = 'none';
    if (elements.authStatusIndicator) elements.authStatusIndicator.style.display = 'none';
    
    // Clear any user data displays
    ['my-bids', 'recent-bids', 'recent-bids-list'].forEach(id => {
      const element = document.getElementById(id);
      if (element) {
        element.innerHTML = '';
      }
    });
  }
}

// Modal handlers for original UI
const modalHandlers = {
  showLogin: () => {
    if (elements.loginModal) elements.loginModal.style.display = 'block';
  },
  hideLogin: () => {
    if (elements.loginModal) {
      elements.loginModal.style.display = 'none';
      if (elements.loginFormOriginal) elements.loginFormOriginal.reset();
    }
  },
  showSignup: () => {
    if (elements.signupModal) elements.signupModal.style.display = 'block';
  },
  hideSignup: () => {
    if (elements.signupModal) {
      elements.signupModal.style.display = 'none';
      if (elements.signupForm) elements.signupForm.reset();
    }
  }
};

// Attach modal event listeners from original UI if elements exist
Object.entries({
  'login-btn': 'showLogin',
  'close-login-modal': 'hideLogin',
  'signup-btn': 'showSignup',
  'close-signup-modal': 'hideSignup'
}).forEach(([id, handler]) => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener('click', modalHandlers[handler]);
  }
});

// Utility functions
function sanitizeHTML(str) {
  const temp = document.createElement('div');
  temp.textContent = str;
  return temp.innerHTML;
}

function getRandomCoordinates() {
  return {
    lat: parseFloat((Math.random() * 180 - 90).toFixed(6)),
    lon: parseFloat((Math.random() * 360 - 180).toFixed(6))
  };
}

function displayResponse(data) {
  if (!elements.responseDiv) return;
  
  elements.responseDiv.innerHTML = '';
  
  const pre = document.createElement('pre');
  pre.className = 'response-content';
  
  const formattedJson = JSON.stringify(data, null, 2);
  pre.textContent = formattedJson;
  
  elements.responseDiv.appendChild(pre);
  
  // Auto scroll to response
  elements.responseDiv.scrollIntoView({ behavior: 'smooth' });
}

// Start status check interval
const statusCheckInterval = setInterval(checkApiStatus, 60000);

// Cleanup on page unload
window.addEventListener('unload', () => {
  clearInterval(statusCheckInterval);
});

// Export for testing if in Node environment
if (typeof module !== 'undefined') {
  module.exports = {
    makeApiRequest,
    checkApiStatus,
    getRandomCoordinates
  };
}