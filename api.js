// RSE Unified API Service
class RSEApiService {
    constructor() {
        // Use HTTPS to avoid security warnings
        this.baseURL = 'https://rse-api.com:5002';
        this.token = this.getStoredToken();
    }

    // Token management
    getStoredToken() {
        return localStorage.getItem('rse_auth_token');
    }

    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('rse_auth_token', token);
        } else {
            localStorage.removeItem('rse_auth_token');
        }
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('rse_auth_token');
    }

    // HTTP request wrapper
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token && !config.headers.Authorization) {
            config.headers.Authorization = `Bearer ${this.token}`;
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    }

    // Authentication endpoints
    async register(username, password) {
        return this.makeRequest('/register', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
    }

    async login(username, password) {
        const response = await this.makeRequest('/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (response.access_token) {
            this.setToken(response.access_token);
        }
        
        return response;
    }

    async logout() {
        this.clearToken();
        return { success: true };
    }

    // Account management
    async getAccountData() {
        return this.makeRequest('/account_data');
    }

    // Buyer endpoints
    async submitBid(bidData) {
        return this.makeRequest('/make_bid', {
            method: 'POST',
            body: JSON.stringify(bidData)
        });
    }

    async cancelBid(bidId) {
        return this.makeRequest('/cancel_bid', {
            method: 'POST',
            body: JSON.stringify({ bid_id: bidId })
        });
    }

    // Seller endpoints
    async grabJob(robotData) {
        return this.makeRequest('/grab_job', {
            method: 'POST',
            body: JSON.stringify(robotData)
        });
    }

    // Shared endpoints
    async getNearbyActivity(lat, lon) {
        return this.makeRequest('/nearby', {
            method: 'POST',
            body: JSON.stringify({ lat, lon })
        });
    }

    async signJob(jobId, starRating) {
        return this.makeRequest('/sign_job', {
            method: 'POST',
            body: JSON.stringify({ 
                job_id: jobId, 
                star_rating: starRating 
            })
        });
    }

    // Communication endpoints
    async sendMessage(recipient, message) {
        return this.makeRequest('/chat', {
            method: 'POST',
            body: JSON.stringify({ recipient, message })
        });
    }

    async getChatMessages() {
        return this.makeRequest('/chat');
    }

    async postBulletin(title, content, category) {
        return this.makeRequest('/bulletin', {
            method: 'POST',
            body: JSON.stringify({ title, content, category })
        });
    }

    async getBulletinPosts(category = null, limit = 20) {
        const params = new URLSearchParams();
        if (category) params.append('category', category);
        if (limit) params.append('limit', limit);
        
        const endpoint = `/bulletin${params.toString() ? '?' + params.toString() : ''}`;
        return this.makeRequest(endpoint);
    }

    // System check
    async ping() {
        return this.makeRequest('/ping');
    }

    // Utility methods
    isAuthenticated() {
        return !!this.token;
    }

    async checkConnection() {
        try {
            await this.ping();
            return true;
        } catch (error) {
            console.warn('API connection check failed:', error);
            return false;
        }
    }
}

// Create global API instance
window.rseApi = new RSEApiService();
