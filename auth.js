// RSE Unified Authentication Manager
class RSEAuthManager {
    constructor() {
        this.currentUser = null;
        this.loginForm = null;
        this.registerForm = null;
        this.userProfile = null;
        this.authStatus = null;
        
        this.initializeElements();
        this.bindEvents();
        this.checkAuthStatus();
    }

    initializeElements() {
        // Auth sections
        this.loginSection = document.getElementById('login-section');
        this.registerSection = document.getElementById('register-section');
        this.profileSection = document.getElementById('profile-section');
        
        // Forms
        this.loginForm = document.getElementById('login-form');
        this.registerForm = document.getElementById('register-form');
        
        // Form links
        this.showRegisterLink = document.getElementById('show-register');
        this.showLoginLink = document.getElementById('show-login');
        this.registerCTA = document.getElementById('register-cta');
        
        // User profile elements
        this.profileUsername = document.getElementById('profile-username');
        this.userRating = document.getElementById('user-rating');
        this.userTotalRatings = document.getElementById('user-total-ratings');
        this.logoutBtn = document.getElementById('logout-btn');
        
        // Auth status indicator
        this.authStatus = document.getElementById('auth-status');
        
        // Message containers
        this.loginMessage = document.getElementById('login-message');
        this.registerMessage = document.getElementById('register-message');
    }

    bindEvents() {
        // Form submissions
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        if (this.registerForm) {
            this.registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }
        
        // Form toggles
        if (this.showRegisterLink) {
            this.showRegisterLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterForm();
            });
        }
        
        if (this.showLoginLink) {
            this.showLoginLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginForm();
            });
        }
        
        if (this.registerCTA) {
            this.registerCTA.addEventListener('click', (e) => {
                e.preventDefault();
                this.showAuthPanel();
                this.showRegisterForm();
            });
        }
        
        // Logout
        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }

    async handleLogin(event) {
        event.preventDefault();
        
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        
        if (!username || !password) {
            this.showMessage(this.loginMessage, 'Please enter both username and password', 'error');
            return;
        }
        
        try {
            this.showMessage(this.loginMessage, 'Logging in...', 'info');
            
            const response = await window.rseApi.login(username, password);
            
            if (response.access_token) {
                this.showMessage(this.loginMessage, 'Login successful!', 'success');
                await this.loadUserProfile(username);
                this.showUserProfile();
                this.updateAuthStatus(true);
                
                // Clear form
                this.loginForm.reset();
                
                // Hide auth panel after delay
                setTimeout(() => {
                    this.hideAuthPanel();
                }, 1500);
            }
        } catch (error) {
            this.showMessage(this.loginMessage, error.message, 'error');
        }
    }

    async handleRegister(event) {
        event.preventDefault();
        
        const username = document.getElementById('register-username').value.trim();
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm').value;
        
        // Validation
        if (!username || !password || !confirmPassword) {
            this.showMessage(this.registerMessage, 'Please fill in all fields', 'error');
            return;
        }
        
        if (username.length < 3 || username.length > 20) {
            this.showMessage(this.registerMessage, 'Username must be 3-20 characters', 'error');
            return;
        }
        
        if (password.length < 8) {
            this.showMessage(this.registerMessage, 'Password must be at least 8 characters', 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showMessage(this.registerMessage, 'Passwords do not match', 'error');
            return;
        }
        
        try {
            this.showMessage(this.registerMessage, 'Creating account...', 'info');
            
            await window.rseApi.register(username, password);
            
            this.showMessage(this.registerMessage, 'Account created successfully! Please log in.', 'success');
            
            // Clear form and switch to login
            this.registerForm.reset();
            
            setTimeout(() => {
                this.showLoginForm();
                // Pre-fill username
                document.getElementById('login-username').value = username;
            }, 2000);
            
        } catch (error) {
            this.showMessage(this.registerMessage, error.message, 'error');
        }
    }

    async handleLogout() {
        try {
            await window.rseApi.logout();
            this.currentUser = null;
            this.showLoginForm();
            this.updateAuthStatus(false);
            this.hideAuthPanel();
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    async loadUserProfile(username) {
        try {
            const accountData = await window.rseApi.getAccountData();
            
            this.currentUser = {
                username: username,
                rating: accountData.stars || 0,
                totalRatings: accountData.total_ratings || 0,
                ...accountData
            };
            
            this.updateProfileDisplay();
        } catch (error) {
            console.error('Failed to load user profile:', error);
            this.currentUser = { username: username, rating: 0, totalRatings: 0 };
            this.updateProfileDisplay();
        }
    }

    updateProfileDisplay() {
        if (!this.currentUser) return;
        
        if (this.profileUsername) {
            this.profileUsername.textContent = this.currentUser.username;
        }
        
        if (this.userRating) {
            this.userRating.textContent = `${this.currentUser.rating}/5`;
        }
        
        if (this.userTotalRatings) {
            this.userTotalRatings.textContent = this.currentUser.totalRatings;
        }
    }

    showLoginForm() {
        this.hideAllSections();
        if (this.loginSection) {
            this.loginSection.style.display = 'block';
        }
        this.clearMessages();
    }

    showRegisterForm() {
        this.hideAllSections();
        if (this.registerSection) {
            this.registerSection.style.display = 'block';
        }
        this.clearMessages();
    }

    showUserProfile() {
        this.hideAllSections();
        if (this.profileSection) {
            this.profileSection.style.display = 'block';
        }
        this.clearMessages();
    }

    hideAllSections() {
        [this.loginSection, this.registerSection, this.profileSection].forEach(section => {
            if (section) section.style.display = 'none';
        });
    }

    showAuthPanel() {
        const authPanel = document.getElementById('auth-panel');
        if (authPanel && !authPanel.classList.contains('show')) {
            const collapse = new bootstrap.Collapse(authPanel);
            collapse.show();
        }
    }

    hideAuthPanel() {
        const authPanel = document.getElementById('auth-panel');
        if (authPanel && authPanel.classList.contains('show')) {
            const collapse = new bootstrap.Collapse(authPanel);
            collapse.hide();
        }
    }

    updateAuthStatus(isAuthenticated) {
        if (this.authStatus) {
            this.authStatus.style.display = isAuthenticated ? 'block' : 'none';
        }
    }

    showMessage(container, message, type = 'info') {
        if (!container) return;
        
        container.textContent = message;
        container.className = `auth-message ${type}`;
        container.style.display = 'block';
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                container.style.display = 'none';
            }, 3000);
        }
    }

    clearMessages() {
        [this.loginMessage, this.registerMessage].forEach(msg => {
            if (msg) {
                msg.style.display = 'none';
                msg.textContent = '';
            }
        });
    }

    async checkAuthStatus() {
        if (window.rseApi.isAuthenticated()) {
            try {
                // Try to load user profile to verify token is still valid
                const accountData = await window.rseApi.getAccountData();
                
                // Extract username from token or use a default
                const username = localStorage.getItem('rse_username') || 'User';
                
                await this.loadUserProfile(username);
                this.showUserProfile();
                this.updateAuthStatus(true);
            } catch (error) {
                // Token is invalid, clear it
                window.rseApi.clearToken();
                this.showLoginForm();
                this.updateAuthStatus(false);
            }
        } else {
            this.showLoginForm();
            this.updateAuthStatus(false);
        }
    }

    // Public methods for other modules
    getCurrentUser() {
        return this.currentUser;
    }

    isLoggedIn() {
        return !!this.currentUser && window.rseApi.isAuthenticated();
    }

    requireAuth() {
        if (!this.isLoggedIn()) {
            this.showAuthPanel();
            this.showLoginForm();
            return false;
        }
        return true;
    }
}

// Initialize authentication manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rseAuth = new RSEAuthManager();
});