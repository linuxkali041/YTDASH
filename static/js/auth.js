/**
 * Authentication Manager
 * Handles OAuth login flow and session management
 */

class AuthManager {
    constructor() {
        this.sessionId = null;
        this.authenticated = false;
        this.userEmail = null;

        this.init();
    }

    /**
     * Initialize auth manager
     */
    init() {
        // Get session ID from app
        if (window.app) {
            this.sessionId = window.app.getSessionId();
        }

        // Setup event listeners
        this.setupEventListeners();

        // Check auth status
        this.checkAuthStatus();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Login button
        const loginBtn = document.getElementById('loginBtn');
        if (loginBtn) {
            loginBtn.addEventListener('click', () => {
                this.initiateLogin();
            });
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                this.logout();
            });
        }
    }

    /**
     * Check authentication status
     */
    async checkAuthStatus() {
        if (!this.sessionId) {
            this.updateAuthState(false);
            return;
        }

        try {
            const response = await window.api.getAuthStatus(this.sessionId);

            this.authenticated = response.authenticated || false;
            this.userEmail = response.user_email || null;

            this.updateAuthState(this.authenticated);

            if (this.authenticated) {
                console.log('Authenticated as:', this.userEmail);
            }
        } catch (error) {
            console.error('Auth status check failed:', error);
            this.updateAuthState(false);
        }
    }

    /**
     * Initiate OAuth login flow
     */
    async initiateLogin() {
        try {
            window.ui.showToast('info', 'Redirecting...', 'Opening login page');

            // Get authorization URL
            const response = await window.api.login();

            if (response.authorization_url) {
                // Redirect to OAuth authorization URL
                window.location.href = response.authorization_url;
            } else {
                throw new Error('No authorization URL received');
            }
        } catch (error) {
            console.error('Login failed:', error);

            let message = 'Failed to initiate login';
            if (error.status === 500 && error.data?.detail?.includes('OAuth not configured')) {
                message = 'OAuth not configured. Please set up Google OAuth credentials.';
            }

            window.ui.showToast('error', 'Login Failed', message);
        }
    }

    /**
     * Logout
     */
    async logout() {
        if (!this.sessionId) {
            return;
        }

        try {
            await window.api.logout(this.sessionId);

            // Clear session
            this.sessionId = null;
            this.authenticated = false;
            this.userEmail = null;

            if (window.app) {
                window.app.clearSession();
            }

            this.updateAuthState(false);

            window.ui.showToast('success', 'Logged Out', 'You have been logged out successfully');
        } catch (error) {
            console.error('Logout failed:', error);
            window.ui.showToast('error', 'Logout Failed', 'Failed to logout. Please try again.');
        }
    }

    /**
     * Update UI based on auth state
     * @param {boolean} authenticated
     */
    updateAuthState(authenticated) {
        this.authenticated = authenticated;

        if (window.ui) {
            window.ui.updateAuthStatus(authenticated, this.userEmail);
        }
    }

    /**
     * Get session ID
     * @returns {string|null}
     */
    getSessionId() {
        return this.sessionId;
    }

    /**
     * Check if authenticated
     * @returns {boolean}
     */
    isAuthenticated() {
        return this.authenticated;
    }
}

// Create global auth manager instance
let authManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        authManager = new AuthManager();
        window.authManager = authManager;
    });
} else {
    authManager = new AuthManager();
    window.authManager = authManager;
}
