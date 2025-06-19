// RSE Unified Main Application
class RSEMainApp {
    constructor() {
        this.themeContainer = null;
        this.currentTheme = 'light';
        
        this.initializeApp();
        this.bindGlobalEvents();
        this.loadTheme();
    }

    initializeApp() {
        this.themeContainer = document.getElementById('theme-container');
        
        // Initialize components
        this.initializeCarousel();
        this.initializeAnimations();
        this.checkApiConnection();
    }

    bindGlobalEvents() {
        // Theme toggle (if theme picker exists)
        document.addEventListener('click', (e) => {
            if (e.target.matches('.theme-toggle')) {
                this.toggleTheme();
            }
        });

        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });

        // Handle external API links
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="check-api-status"]')) {
                e.preventDefault();
                this.checkApiStatus(e.target);
            }
        });

        // Auto-hide alerts after delay
        this.autoHideAlerts();
    }

    initializeCarousel() {
        const carousel = document.getElementById('news-carousel');
        if (carousel) {
            // Auto-advance carousel
            setInterval(() => {
                const nextBtn = carousel.querySelector('.carousel-control-next');
                if (nextBtn) nextBtn.click();
            }, 5000);
        }
    }

    initializeAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe sections for animation
        document.querySelectorAll('.content-section, .service-card, .guide-card').forEach(el => {
            observer.observe(el);
        });
    }

    async checkApiConnection() {
        try {
            const isConnected = await window.rseApi.checkConnection();
            this.updateConnectionStatus(isConnected);
        } catch (error) {
            console.warn('Failed to check API connection:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(isConnected) {
        // Create or update connection indicator
        let indicator = document.getElementById('connection-status');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'connection-status';
            indicator.className = 'connection-indicator';
            document.body.appendChild(indicator);
        }

        indicator.className = `connection-indicator ${isConnected ? 'connected' : 'disconnected'}`;
        indicator.title = isConnected ? 'API Connected' : 'API Disconnected';
        
        // Auto-hide after delay if connected
        if (isConnected) {
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 3000);
        }
    }

    async checkApiStatus(button) {
        const originalText = button.textContent;
        const targetId = button.getAttribute('data-target');
        const responseContainer = document.getElementById(targetId);

        try {
            button.textContent = 'Checking...';
            button.disabled = true;

            const response = await window.rseApi.ping();
            
            if (responseContainer) {
                responseContainer.innerHTML = `
                    <div class="alert alert-success">
                        <strong>API Status:</strong> ${response.message || 'OK'}
                        <br><small>Response time: ${Date.now() % 1000}ms</small>
                    </div>
                `;
            }
        } catch (error) {
            if (responseContainer) {
                responseContainer.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>API Error:</strong> ${error.message}
                    </div>
                `;
            }
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.saveTheme();
    }

    applyTheme() {
        if (this.themeContainer) {
            this.themeContainer.className = `${this.currentTheme}-theme`;
        }
        
        // Update theme color meta tag
        const themeColor = this.currentTheme === 'dark' ? '#212529' : '#ffffff';
        this.updateMetaThemeColor(themeColor);
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('rse_theme');
        if (savedTheme) {
            this.currentTheme = savedTheme;
        } else {
            // Auto-detect system preference
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                this.currentTheme = 'dark';
            }
        }
        this.applyTheme();
    }

    saveTheme() {
        localStorage.setItem('rse_theme', this.currentTheme);
    }

    updateMetaThemeColor(color) {
        let meta = document.querySelector('meta[name="theme-color"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.name = 'theme-color';
            document.head.appendChild(meta);
        }
        meta.content = color;
    }

    autoHideAlerts() {
        // Auto-hide success alerts after 5 seconds
        setTimeout(() => {
            document.querySelectorAll('.alert-success').forEach(alert => {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000);
    }

    // Utility methods for other modules
    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">&times;</button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Position notification
        const notifications = document.querySelectorAll('.notification');
        notification.style.cssText = `
            position: fixed;
            top: ${80 + (notifications.length - 1) * 60}px;
            right: 20px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: var(--border-radius);
            padding: var(--spacing-md);
            box-shadow: var(--box-shadow-lg);
            z-index: 1000;
            max-width: 300px;
            transform: translateX(100%);
            transition: transform 0.3s ease;
        `;

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        // Auto-remove
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }

        return notification;
    }

    removeNotification(notification) {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }

    showLoading(container, message = 'Loading...') {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            container.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <span>${message}</span>
                </div>
            `;
        }
    }

    hideLoading(container) {
        if (typeof container === 'string') {
            container = document.getElementById(container);
        }
        
        if (container) {
            const spinner = container.querySelector('.loading-spinner');
            if (spinner) {
                spinner.remove();
            }
        }
    }

    // Error handling
    handleError(error, context = '') {
        console.error(`RSE Error ${context}:`, error);
        this.showNotification(
            `Error ${context}: ${error.message}`,
            'error',
            5000
        );
    }

    // Navigation helpers
    navigateTo(page) {
        if (page.startsWith('http')) {
            window.open(page, '_blank');
        } else {
            window.location.href = page;
        }
    }

    // Data formatting utilities
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    }

    formatDate(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    formatDistance(distance) {
        return distance < 1 
            ? `${(distance * 5280).toFixed(0)} ft`
            : `${distance.toFixed(1)} mi`;
    }

    // Location utilities
    async getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                position => {
                    resolve({
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    });
                },
                error => {
                    reject(new Error(`Location error: ${error.message}`));
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 300000 // 5 minutes
                }
            );
        });
    }
}

// Add CSS for notifications and loading spinner
const utilityStyles = `
<style>
.notification {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-sm);
}

.notification-close {
    background: none;
    border: none;
    font-size: 1.2rem;
    cursor: pointer;
    color: var(--text-secondary);
}

.notification-info { border-left: 4px solid var(--primary-color); }
.notification-success { border-left: 4px solid var(--success-color); }
.notification-warning { border-left: 4px solid var(--warning-color); }
.notification-error { border-left: 4px solid var(--danger-color); }

.loading-spinner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-xl);
}

.spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top: 3px solid var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.connection-indicator {
    position: fixed;
    bottom: 20px;
    left: 20px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    z-index: 1000;
    transition: opacity 0.3s ease;
}

.connection-indicator.connected {
    background-color: var(--success-color);
}

.connection-indicator.disconnected {
    background-color: var(--danger-color);
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}
</style>
`;

// Inject utility styles
document.head.insertAdjacentHTML('beforeend', utilityStyles);

// Initialize main application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rseApp = new RSEMainApp();
});