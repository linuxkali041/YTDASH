/**
 * Main Application Controller
 * Handles app initialization, theme management, and settings
 */

class App {
    constructor() {
        this.currentTheme = 'light';
        this.settings = {
            defaultQuality: 'best',
            theme: 'light'
        };
        this.sessionId = null;
        
        this.init();
    }

    /**
     * Initialize application
     */
    init() {
        // Load settings from localStorage
        this.loadSettings();
        
        // Apply theme
        this.applyTheme(this.settings.theme);
        
        // Check for session ID in URL (from OAuth callback)
        this.checkURLParams();
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check auth status
        if (window.authManager) {
            window.authManager.checkAuthStatus();
        }
        
        console.log('App initialized');
    }

    /**
     * Load settings from localStorage
     */
    loadSettings() {
        const savedSettings = localStorage.getItem('ytdl_settings');
        if (savedSettings) {
            try {
                this.settings = JSON.parse(savedSettings);
            } catch (e) {
                console.error('Failed to parse saved settings:', e);
            }
        }
    }

    /**
     * Save settings to localStorage
     */
    saveSettings() {
        localStorage.setItem('ytdl_settings', JSON.stringify(this.settings));
    }

    /**
     * Apply theme to document
     * @param {string} theme - Theme name (light, dark, amoled)
     */
    applyTheme(theme) {
        // Update data-theme attribute
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update current theme
        this.currentTheme = theme;
        this.settings.theme = theme;
        
        // Update theme toggle buttons
        document.querySelectorAll('.theme-option').forEach(btn => {
            if (btn.dataset.theme === theme) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Save settings
        this.saveSettings();
    }

    /**
     * Check URL parameters (for OAuth callback)
     */
    checkURLParams() {
        const params = new URLSearchParams(window.location.search);
        
        // Check for session ID from OAuth
        const sessionId = params.get('session_id');
        if (sessionId) {
            this.sessionId = sessionId;
            localStorage.setItem('ytdl_session_id', sessionId);
            
            // Show success message
            if (params.get('auth') === 'success') {
                window.ui.showToast('success', 'Login Successful', 'You are now authenticated');
            }
            
            // Clean up URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else {
            // Try to get from localStorage
            this.sessionId = localStorage.getItem('ytdl_session_id');
        }
        
        // Check for auth failure
        if (params.get('auth') === 'failed') {
            const error = params.get('error') || 'Unknown error';
            window.ui.showToast('error', 'Login Failed', error);
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Theme toggle buttons
        document.querySelectorAll('.theme-option').forEach(btn => {
            btn.addEventListener('click', () => {
                this.applyTheme(btn.dataset.theme);
            });
        });

        // Settings button
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => {
                this.openSettings();
            });
        }

        // Settings modal close
        const settingsModal = document.getElementById('settingsModal');
        if (settingsModal) {
            const closeBtn = settingsModal.querySelector('.modal-close');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.closeSettings();
                });
            }

            // Close on overlay click
            settingsModal.addEventListener('click', (e) => {
                if (e.target === settingsModal) {
                    this.closeSettings();
                }
            });
        }

        // Default quality setting
        const defaultQualitySelect = document.getElementById('defaultQuality');
        if (defaultQualitySelect) {
            defaultQualitySelect.value = this.settings.defaultQuality;
            defaultQualitySelect.addEventListener('change', () => {
                this.settings.defaultQuality = defaultQualitySelect.value;
                this.saveSettings();
                window.ui.showToast('success', 'Settings Saved', 'Default quality updated');
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Escape key closes modals
            if (e.key === 'Escape') {
                this.closeSettings();
            }
        });
    }

    /**
     * Open settings modal
     */
    openSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('active');
            
            // Update theme buttons in modal
            modal.querySelectorAll('.theme-option').forEach(btn => {
                if (btn.dataset.theme === this.currentTheme) {
                    btn.classList.add('active');
                } else {
                    btn.classList.remove('active');
                }
            });
            
            // Set focus to close button for accessibility
            setTimeout(() => {
                const closeBtn = modal.querySelector('.modal-close');
                if (closeBtn) closeBtn.focus();
            }, 100);
        }
    }

    /**
     * Close settings modal
     */
    closeSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.remove('active');
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
     * Set session ID
     * @param {string} sessionId
     */
    setSessionId(sessionId) {
        this.sessionId = sessionId;
        if (sessionId) {
            localStorage.setItem('ytdl_session_id', sessionId);
        } else {
            localStorage.removeItem('ytdl_session_id');
        }
    }

    /**
     * Clear session
     */
    clearSession() {
        this.sessionId = null;
        localStorage.removeItem('ytdl_session_id');
    }
}

// Initialize app when DOM is ready
let app;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        app = new App();
        window.app = app;
    });
} else {
    app = new App();
    window.app = app;
}
