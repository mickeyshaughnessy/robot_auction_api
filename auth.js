// Shared Authentication Module for RSE
// Include this file in all pages that need authentication

const RSE_AUTH = {
    API_URL: 'http://100.26.236.1:5001',
    
    // Get authentication token from storage
    getToken() {
        const possibleKeys = [
            'authToken', 'access_token', 'token', 'jwt', 'bearer_token', 'userToken'
        ];
        
        for (const key of possibleKeys) {
            let token = localStorage.getItem(key) || sessionStorage.getItem(key);
            if (token) return token;
        }
        
        // Check for tokens in JSON objects
        const possibleAuthObjects = ['auth', 'authentication', 'session', 'login', 'user'];
        for (const key of possibleAuthObjects) {
            const value = localStorage.getItem(key) || sessionStorage.getItem(key);
            if (value) {
                try {
                    const parsed = JSON.parse(value);
                    if (parsed.token || parsed.access_token || parsed.authToken) {
                        return parsed.token || parsed.access_token || parsed.authToken;
                    }
                } catch (e) {
                    // Not JSON, might be direct token
                    if (value.length > 20) return value;
                }
            }
        }
        
        return null;
    },
    
    // Get current username from storage
    getUsername() {
        const possibleKeys = ['currentUser', 'username', 'user', 'loggedInUser'];
        
        for (const key of possibleKeys) {
            let username = localStorage.getItem(key) || sessionStorage.getItem(key);
            if (username) {
                try {
                    const parsed = JSON.parse(username);
                    return parsed.username || parsed.name || parsed;
                } catch (e) {
                    return username;
                }
            }
        }
        
        return null;
    },
    
    // Store authentication data
    setAuth(token, username) {
        localStorage.setItem('authToken', token);
        localStorage.setItem('currentUser', username);
    },
    
    // Clear authentication data
    clearAuth() {
        const keysToRemove = [
            'authToken', 'access_token', 'token', 'jwt', 'bearer_token', 'userToken',
            'currentUser', 'username', 'user', 'loggedInUser', 'auth', 'authentication', 'session'
        ];
        
        keysToRemove.forEach(key => {
            localStorage.removeItem(key);
            sessionStorage.removeItem(key);
        });
    },
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    },
    
    // Make authenticated API call
    async apiCall(endpoint, options = {}) {
        const token = this.getToken();
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                ...(token && { 'Authorization': `Bearer ${token}` })
            }
        };
        
        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: { ...defaultOptions.headers, ...options.headers }
        };
        
        const response = await fetch(`${this.API_URL}${endpoint}`, mergedOptions);
        
        if (response.status === 401) {
            this.clearAuth();
            throw new Error('Authentication expired. Please log in again.');
        }
        
        return response;
    },
    
    // Debug function to log all auth-related storage
    debugAuth() {
        console.log('=== RSE AUTH DEBUG ===');
        console.log('Token:', this.getToken() ? this.getToken().substring(0, 30) + '...' : 'None');
        console.log('Username:', this.getUsername() || 'None');
        console.log('Is Authenticated:', this.isAuthenticated());
        
        console.log('All localStorage:');
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            console.log(`  ${key}:`, localStorage.getItem(key));
        }
        
        console.log('All sessionStorage:');
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            console.log(`  ${key}:`, sessionStorage.getItem(key));
        }
        console.log('=== END AUTH DEBUG ===');
    }
};

// Auto-initialize debugging if in development
if (window.location.hostname === 'localhost' || window.location.hostname.includes('robotservicesauction.com')) {
    RSE_AUTH.debugAuth();
}