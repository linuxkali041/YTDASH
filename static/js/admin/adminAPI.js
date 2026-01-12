/**
 * Admin API Client
 * Handles all API calls to admin endpoints
 */

class AdminAPI {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * Get authorization header with token
     */
    getAuthHeader() {
        const token = localStorage.getItem('access_token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Make authenticated request
     */
    async request(method, endpoint, body = null) {
        const config = {
            method,
            headers: this.getAuthHeader()
        };

        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(this.baseURL + endpoint, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error(`Admin API Error (${method} ${endpoint}):`, error);
            throw error;
        }
    }

    // ============================================
    // User Management
    // ============================================

    async getUsers(skip = 0, limit = 50, filters = {}) {
        const params = new URLSearchParams({ skip, limit, ...filters });
        return this.request('GET', `/admin/users?${params}`);
    }

    async getUser(userId) {
        return this.request('GET', `/admin/users/${userId}`);
    }

    async createUser(userData) {
        return this.request('POST', '/admin/users', userData);
    }

    async updateUser(userId, updates) {
        return this.request('PUT', `/admin/users/${userId}`, updates);
    }

    async deleteUser(userId) {
        return this.request('DELETE', `/admin/users/${userId}`);
    }

    // ============================================
    // Settings Management
    // ============================================

    async getSettings(category = null) {
        const params = category ? `?category=${category}` : '';
        return this.request('GET', `/admin/settings${params}`);
    }

    async updateSetting(key, value) {
        return this.request('PUT', `/admin/settings/${key}`, { value: String(value) });
    }

    // ============================================
    // System Monitoring
    // ============================================

    async getStats() {
        return this.request('GET', '/admin/stats');
    }

    async getDownloads(skip = 0, limit = 50, userId = null) {
        const params = new URLSearchParams({ skip, limit });
        if (userId) params.append('user_id', userId);
        return this.request('GET', `/admin/downloads?${params}`);
    }

    async getLogs(skip = 0, limit = 100, filters = {}) {
        const params = new URLSearchParams({ skip, limit, ...filters });
        return this.request('GET', `/admin/logs?${params}`);
    }

    async clearLogs() {
        return this.request('DELETE', '/admin/logs');
    }
}

// Create global instance
const adminAPI = new AdminAPI();
window.adminAPI = adminAPI;
