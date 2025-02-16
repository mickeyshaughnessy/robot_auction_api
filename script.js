// Constants 
const API_URL = window.location.protocol === 'https:' ? 
  'https://100.26.236.1:5001' : 'http://100.26.236.1:5001';
const API_TIMEOUT = 5000; // 5 second timeout
let authToken = null;

// Cache DOM elements
const elements = {
  loginBtn: document.getElementById('login-btn'),
  signupBtn: document.getElementById('signup-btn'), 
  loginModal: document.getElementById('login-modal'),
  signupModal: document.getElementById('signup-modal'),
  closeLoginModalBtn: document.getElementById('close-login-modal'),
  closeSignupModalBtn: document.getElementById('close-signup-modal'),
  loginForm: document.getElementById('login-form'),
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
});

async function checkApiStatus() {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    const response = await fetch(`${API_URL}/ping`, {
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

async function makeApiRequest(endpoint, method, data = null) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      method,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': `Bearer ${authToken}` })
      },
      ...(data && { body: JSON.stringify(data) })
    });

    clearTimeout(timeoutId);
    const result = await response.json();

    if (response.status === 401) {
      authToken = null;
      updateUI();
      throw new Error('Session expired. Please login again.');
    }

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
    const errorMessage = error.name === 'AbortError' ? 
      'Request timed out' : error.message;
    displayResponse({ error: errorMessage });
    console.error("API Request Error:", error);
    return null;
  }
}

// Form initialization
function initializeForm() {
  setDefaultTimes();
  setRandomServiceDescriptionPlaceholder();
}

function setDefaultTimes() {
  const now = new Date();
  const sevenDaysFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  const formatDateTimeLocal = (date) => {
    return date.toISOString().slice(0, 16);
  };

  elements.startTimeInput.value = formatDateTimeLocal(now);
  elements.endTimeInput.value = formatDateTimeLocal(sevenDaysFromNow);
}

function setRandomServiceDescriptionPlaceholder() {
  try {
    const placeholders = JSON.parse(elements.serviceDescriptionTextarea.getAttribute('data-placeholders'));
    if (Array.isArray(placeholders) && placeholders.length > 0) {
      const randomIndex = Math.floor(Math.random() * placeholders.length);
      elements.serviceDescriptionTextarea.setAttribute('placeholder', placeholders[randomIndex]);
    }
  } catch (error) {
    console.error("Error parsing service descriptions:", error);
    elements.serviceDescriptionTextarea.setAttribute('placeholder', 'Describe the service you want...');
  }
}

// UI Updates
function updateUI() {
  const isLoggedIn = Boolean(authToken);
  elements.loginBtn.textContent = isLoggedIn ? 'Logout' : 'Login';
  elements.signupBtn.style.display = isLoggedIn ? 'none' : 'inline-block';
  
  if (isLoggedIn) {
    Promise.all([fetchMyBids(), fetchRecentBids()]);
  } else {
    ['my-bids', 'recent-bids'].forEach(id => {
      document.getElementById(id).innerHTML = '';
    });
  }
}

// Modal handlers
const modalHandlers = {
  showLogin: () => elements.loginModal.style.display = 'block',
  hideLogin: () => {
    elements.loginModal.style.display = 'none';
    elements.loginForm.reset();
  },
  showSignup: () => elements.signupModal.style.display = 'block',
  hideSignup: () => {
    elements.signupModal.style.display = 'none';
    elements.signupForm.reset();
  }
};

// Attach modal event listeners
Object.entries({
  'login-btn': 'showLogin',
  'close-login-modal': 'hideLogin',
  'signup-btn': 'showSignup',
  'close-signup-modal': 'hideSignup'
}).forEach(([id, handler]) => {
  document.getElementById(id)?.addEventListener('click', modalHandlers[handler]);
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

// Start status check interval
const statusCheckInterval = setInterval(checkApiStatus, 60000);

// Cleanup on page unload
window.addEventListener('unload', () => {
  clearInterval(statusCheckInterval);
});

// Export for testing
if (typeof module !== 'undefined') {
  module.exports = {
    makeApiRequest,
    checkApiStatus,
    getRandomCoordinates
  };
}