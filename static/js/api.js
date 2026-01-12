/**
 * API Communication Layer
 * Handles all HTTP requests to the backend API
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * Make HTTP request
     * @param {string} method - HTTP method
     * @param {string} endpoint - API endpoint
     * @param {object} options - Request options
     * @returns {Promise<object>}
     */
    async request(method, endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        };

        // Add body for POST/PUT requests
        if (options.body) {
            config.body = JSON.stringify(options.body);
        }

        // Add query parameters
        if (options.params) {
            const params = new URLSearchParams(options.params);
            const separator = url.includes('?') ? '&' : '?';
            endpoint = `${endpoint}${separator}${params.toString()}`;
        }

        try {
            const response = await fetch(this.baseURL + endpoint, config);

            // Parse JSON response
            let data;
            try {
                data = await response.json();
            } catch (e) {
                data = {};
            }

            // Handle errors
            if (!response.ok) {
                const error = new Error(data.detail || `HTTP ${response.status}`);
                error.status = response.status;
                error.data = data;
                throw error;
            }

            return data;
        } catch (error) {
            console.error(`API Error (${method} ${endpoint}):`, error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request('GET', endpoint, options);
    }

    /**
     * POST request
     */
    async post(endpoint, body, options = {}) {
        return this.request('POST', endpoint, { ...options, body });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request('DELETE', endpoint, options);
    }

    // ============================================
    // Authentication APIs
    // ============================================

    /**
     * Initiate OAuth login
     * @returns {Promise<object>}
     */
    async login() {
        return this.get('/api/auth/login');
    }

    /**
     * Check authentication status
     * @param {string} sessionId - Session ID
     * @returns {Promise<object>}
     */
    async getAuthStatus(sessionId) {
        return this.get('/api/auth/status', {
            params: sessionId ? { session_id: sessionId } : {}
        });
    }

    /**
     * Logout
     * @param {string} sessionId - Session ID
     * @returns {Promise<object>}
     */
    async logout(sessionId) {
        return this.post('/api/auth/logout', null, {
            params: { session_id: sessionId }
        });
    }

    /**
     * Refresh cookies
     * @param {string} sessionId - Session ID
     * @returns {Promise<object>}
     */
    async refreshCookies(sessionId) {
        return this.post('/api/auth/refresh', null, {
            params: { session_id: sessionId }
        });
    }

    // ============================================
    // Video APIs
    // ============================================

    /**
     * Get video information
     * @param {string} url - YouTube URL
     * @param {string} sessionId - Optional session ID
     * @returns {Promise<object>}
     */
    async getVideoInfo(url, sessionId = null) {
        return this.post('/api/video/info', {
            url,
            session_id: sessionId
        });
    }

    /**
     * Initiate video download
     * @param {object} request - Download request
     * @returns {Promise<object>}
     */
    async downloadVideo(request) {
        return this.post('/api/video/download', request);
    }

    /**
     * Get download progress
     * @param {string} downloadId - Download ID
     * @returns {Promise<object>}
     */
    async getDownloadProgress(downloadId) {
        return this.get(`/api/download/progress/${downloadId}`);
    }

    /**
     * Get download status
     * @param {string} downloadId - Download ID
     * @returns {Promise<object>}
     */
    async getDownloadStatus(downloadId) {
        return this.get(`/api/download/status/${downloadId}`);
    }

    /**
     * Cancel download
     * @param {string} downloadId - Download ID
     * @param {string} sessionId - Session ID
     * @returns {Promise<object>}
     */
    async cancelDownload(downloadId, sessionId = null) {
        return this.delete(`/api/download/${downloadId}`, {
            params: sessionId ? { session_id: sessionId } : {}
        });
    }

    /**
     * Get queue status
     * @returns {Promise<object>}
     */
    async getQueueStatus() {
        return this.get('/api/queue/status');
    }

    // ============================================
    // Playlist APIs
    // ============================================

    /**
     * Get playlist information
     * @param {string} url - YouTube playlist URL
     * @param {string} sessionId - Optional session ID
     * @returns {Promise<object>}
     */
    async getPlaylistInfo(url, sessionId = null) {
        return this.post('/api/playlist/info', {
            url,
            session_id: sessionId
        });
    }

    /**
     * Initiate playlist download
     * @param {object} request - Playlist download request
     * @returns {Promise<object>}
     */
    async downloadPlaylist(request) {
        return this.post('/api/playlist/download', request);
    }

    /**
     * Get playlist download progress
     * @param {string} playlistId - Playlist download ID
     * @returns {Promise<object>}
     */
    async getPlaylistProgress(playlistId) {
        return this.get(`/api/playlist/progress/${playlistId}`);
    }

    /**
     * Health check
     * @returns {Promise<object>}
     */
    async healthCheck() {
        return this.get('/health');
    }

}

// Create global API client instance
const api = new APIClient();
window.api = api;
