/**
 * UI Management
 * Handles UI updates, notifications, and loading states
 */

class UIManager {
    constructor() {
        this.toastContainer = document.getElementById('toastContainer');
        this.toastQueue = [];
        this.maxToasts = 3;
    }

    /**
     * Show toast notification
     * @param {string} type - Toast type (success, error, warning, info)
     * @param {string} title - Toast title
     * @param {string} message - Toast message
     * @param {number} duration - Duration in ms (0 = no auto-dismiss)
     */
    showToast(type = 'info', title, message, duration = 5000) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;

        // Icon based on type
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        toast.innerHTML = `
            <div class="toast-icon">${icons[type] || icons.info}</div>
            <div class="toast-content">
                <div class="toast-title">${this.escapeHtml(title)}</div>
                ${message ? `<div class="toast-message">${this.escapeHtml(message)}</div>` : ''}
            </div>
        `;

        // Add to container
        this.toastContainer.appendChild(toast);
        this.toastQueue.push(toast);

        // Remove excess toasts
        while (this.toastQueue.length > this.maxToasts) {
            const oldToast = this.toastQueue.shift();
            this.removeToast(oldToast);
        }

        // Auto-dismiss if duration specified
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        }

        // Click to dismiss
        toast.addEventListener('click', () => {
            this.removeToast(toast);
        });
    }

    /**
     * Remove toast
     * @param {HTMLElement} toast
     */
    removeToast(toast) {
        if (!toast || !toast.parentNode) return;

        toast.style.animation = 'slideIn 0.3s ease-out reverse';
        setTimeout(() => {
            toast.remove();
            const index = this.toastQueue.indexOf(toast);
            if (index > -1) {
                this.toastQueue.splice(index, 1);
            }
        }, 300);
    }

    /**
     * Show loading state on element
     * @param {HTMLElement} element
     * @param {boolean} loading
     */
    setLoading(element, loading) {
        if (!element) return;

        if (loading) {
            element.classList.add('loading');
            element.disabled = true;
        } else {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }

    /**
     * Show/hide element
     * @param {HTMLElement|string} element - Element or selector
     * @param {boolean} show
     */
    toggleElement(element, show) {
        const el = typeof element === 'string' ? document.querySelector(element) : element;
        if (!el) return;

        if (show) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }

    /**
     * Update progress bar
     * @param {number} percent - Progress percentage (0-100)
     * @param {string} status - Status text
     * @param {object} details - Additional details (speed, eta)
     */
    updateProgress(percent, status = '', details = {}) {
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressSpeed = document.getElementById('progressSpeed');
        const progressETA = document.getElementById('progressETA');
        const progressStatus = document.getElementById('progressStatus');

        if (progressBar) {
            progressBar.style.width = `${percent}%`;
            progressBar.setAttribute('aria-valuenow', percent);
        }

        if (progressPercent) {
            progressPercent.textContent = `${percent.toFixed(1)}%`;
        }

        if (progressSpeed && details.speed) {
            progressSpeed.textContent = details.speed;
        }

        if (progressETA && details.eta) {
            progressETA.textContent = `ETA: ${details.eta}`;
        }

        if (progressStatus) {
            progressStatus.textContent = status;
        }
    }

    /**
     * Reset progress bar
     */
    resetProgress() {
        this.updateProgress(0, '', {});
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.classList.add('hidden');
        }
    }

    /**
     * Show progress section
     */
    showProgress() {
        const progressSection = document.getElementById('progressSection');
        if (progressSection) {
            progressSection.classList.remove('hidden');
        }
    }

    /**
     * Display video information
     * @param {object} videoInfo - Video information object
     */
    displayVideoInfo(videoInfo) {
        // Show video info section
        const videoInfoEl = document.getElementById('videoInfo');
        if (videoInfoEl) {
            videoInfoEl.classList.remove('hidden');
        }

        // Update thumbnail
        const thumbnail = document.getElementById('videoThumbnail');
        if (thumbnail && videoInfo.thumbnail) {
            thumbnail.src = videoInfo.thumbnail;
            thumbnail.classList.remove('hidden');
        }

        // Update title
        const title = document.getElementById('videoTitle');
        if (title) {
            title.textContent = videoInfo.title;
        }

        // Update meta information
        const meta = document.getElementById('videoMeta');
        if (meta) {
            const parts = [];
            if (videoInfo.uploader) parts.push(videoInfo.uploader);
            if (videoInfo.view_count) parts.push(`${this.formatNumber(videoInfo.view_count)} views`);
            if (videoInfo.duration) parts.push(this.formatDuration(videoInfo.duration));
            meta.textContent = parts.join(' • ');
        }

        // Update description
        const description = document.getElementById('videoDescription');
        if (description && videoInfo.description) {
            const shortDesc = videoInfo.description.substring(0, 200);
            description.textContent = shortDesc + (videoInfo.description.length > 200 ? '...' : '');
        }

        // Show format selection
        this.toggleElement('#formatSelection', true);
    }

    /**
     * Update auth status display
     * @param {boolean} authenticated
     * @param {string} userEmail
     */
    updateAuthStatus(authenticated, userEmail = null) {
        const authStatus = document.getElementById('authStatus');
        const authPrompt = document.getElementById('authPromptCard');

        if (authenticated) {
            if (authStatus) {
                authStatus.classList.remove('hidden');
            }
            if (authPrompt) {
                authPrompt.classList.add('hidden');
            }
        } else {
            if (authStatus) {
                authStatus.classList.add('hidden');
            }
            if (authPrompt) {
                authPrompt.classList.remove('hidden');
            }
        }
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} html
     * @returns {string}
     */
    escapeHtml(html) {
        const div = document.createElement('div');
        div.textContent = html;
        return div.innerHTML;
    }

    /**
     * Format number with commas
     * @param {number} num
     * @returns {string}
     */
    formatNumber(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    }

    /**
     * Format duration (seconds to HH:MM:SS)
     * @param {number} seconds
     * @returns {string}
     */
    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    /**
     * Show error message
     * @param {string} message
     * @param {HTMLElement} element - Element to show error near
     */
    showError(message, element = null) {
        this.showToast('error', 'Error', message);

        if (element) {
            const errorEl = element.parentElement?.querySelector('.form-error');
            if (errorEl) {
                errorEl.textContent = message;
                errorEl.classList.remove('hidden');
            }
        }
    }

    /**
     * Clear error message
     * @param {HTMLElement} element
     */
    clearError(element) {
        if (!element) return;

        const errorEl = element.parentElement?.querySelector('.form-error');
        if (errorEl) {
            errorEl.textContent = '';
            errorEl.classList.add('hidden');
        }
    }
}

// Create global UI manager instance
const ui = new UIManager();
window.ui = ui;
