/**
 * Download Manager
 * Handles video info fetching and download flow
 */

class DownloadManager {
    constructor() {
        this.currentVideoInfo = null;
        this.currentDownloadId = null;
        this.progressInterval = null;

        this.init();
    }

    /**
     * Initialize download manager
     */
    init() {
        this.setupEventListeners();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Get video info button
        const getInfoBtn = document.getElementById('getInfoBtn');
        if (getInfoBtn) {
            getInfoBtn.addEventListener('click', () => {
                this.getVideoInfo();
            });
        }

        // Download form
        const downloadForm = document.getElementById('downloadForm');
        if (downloadForm) {
            downloadForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.initiateDownload();
            });
        }

        // URL input - clear errors on input
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.addEventListener('input', () => {
                window.ui.clearError(urlInput);
            });
        }

        // Format type change
        const formatType = document.getElementById('formatType');
        if (formatType) {
            formatType.addEventListener('change', () => {
                this.updateFormatOptions();
            });
        }
    }

    /**
     * Get video information
     */
    async getVideoInfo() {
        const urlInput = document.getElementById('urlInput');
        const getInfoBtn = document.getElementById('getInfoBtn');

        if (!urlInput || !urlInput.value.trim()) {
            window.ui.showError('Please enter a YouTube URL', urlInput);
            return;
        }

        const url = urlInput.value.trim();

        // Clear previous errors
        window.ui.clearError(urlInput);

        // Show loading state
        window.ui.setLoading(getInfoBtn, true);

        try {
            // Get session ID if authenticated
            const sessionId = window.app ? window.app.getSessionId() : null;

            // Fetch video info
            const videoInfo = await window.api.getVideoInfo(url, sessionId);

            // Store video info
            this.currentVideoInfo = videoInfo;

            // Display video info
            window.ui.displayVideoInfo(videoInfo);

            window.ui.showToast('success', 'Video Found', 'Video information loaded successfully');
        } catch (error) {
            console.error('Failed to get video info:', error);

            let errorMessage = 'Failed to fetch video information';

            if (error.status === 400) {
                errorMessage = 'Invalid YouTube URL';
            } else if (error.status === 404) {
                errorMessage = 'Video not found or unavailable';
            } else if (error.status === 429) {
                errorMessage = 'Rate limit exceeded. Please try again later.';
            }

            window.ui.showError(errorMessage, urlInput);
        } finally {
            window.ui.setLoading(getInfoBtn, false);
        }
    }

    /**
     * Update format options based on selected type
     */
    updateFormatOptions() {
        const formatType = document.getElementById('formatType');
        const qualityGroup = document.getElementById('qualityGroup');
        const qualitySelect = document.getElementById('quality');

        if (!formatType || !qualitySelect) return;

        const isAudio = formatType.value === 'audio';

        if (isAudio) {
            // Audio quality options
            qualitySelect.innerHTML = `
                <option value="best">Best Quality</option>
                <option value="192">192 kbps</option>
                <option value="128">128 kbps</option>
                <option value="96">96 kbps</option>
            `;
            if (qualityGroup) {
                qualityGroup.querySelector('.form-label').textContent = 'Audio Quality';
            }
        } else {
            // Video quality options
            qualitySelect.innerHTML = `
                <option value="best">Best Quality</option>
                <option value="2160p">2160p (4K)</option>
                <option value="1440p">1440p (2K)</option>
                <option value="1080p">1080p (Full HD)</option>
                <option value="720p">720p (HD)</option>
                <option value="480p">480p</option>
                <option value="360p">360p</option>
            `;
            if (qualityGroup) {
                qualityGroup.querySelector('.form-label').textContent = 'Video Quality';
            }
        }
    }

    /**
     * Initiate download
     */
    async initiateDownload() {
        if (!this.currentVideoInfo) {
            window.ui.showToast('warning', 'No Video Selected', 'Please fetch video information first');
            return;
        }

        const urlInput = document.getElementById('urlInput');
        const downloadBtn = document.getElementById('downloadBtn');
        const formatType = document.getElementById('formatType');
        const quality = document.getElementById('quality');

        if (!urlInput || !downloadBtn) return;

        // Get download options
        const downloadRequest = {
            url: urlInput.value.trim(),
            format_type: formatType?.value || 'video',
            quality: quality?.value || 'best',
            session_id: window.app ? window.app.getSessionId() : null
        };

        // Show loading state
        window.ui.setLoading(downloadBtn, true);

        try {
            // Initiate download
            const response = await window.api.downloadVideo(downloadRequest);

            this.currentDownloadId = response.download_id;

            // Show progress section
            window.ui.showProgress();
            window.ui.updateProgress(0, 'Download queued...');

            // Start polling for progress
            this.startProgressPolling();

            window.ui.showToast('success', 'Download Started', 'Your download has been queued');
        } catch (error) {
            console.error('Failed to initiate download:', error);

            let errorMessage = 'Failed to start download';

            if (error.status === 429) {
                errorMessage = 'Maximum concurrent downloads reached. Please wait.';
            } else if (error.status === 401) {
                errorMessage = 'Authentication required for this video';
            } else if (error.data?.detail) {
                errorMessage = error.data.detail;
            }

            window.ui.showToast('error', 'Download Failed', errorMessage);
        } finally {
            window.ui.setLoading(downloadBtn, false);
        }
    }

    /**
     * Start polling for download progress
     */
    startProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        this.progressInterval = setInterval(async () => {
            await this.updateDownloadProgress();
        }, 1000); // Poll every second
    }

    /**
     * Stop polling for download progress
     */
    stopProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    /**
     * Update download progress
     */
    async updateDownloadProgress() {
        if (!this.currentDownloadId) {
            this.stopProgressPolling();
            return;
        }

        try {
            const progress = await window.api.getDownloadProgress(this.currentDownloadId);

            // Update progress bar
            const percent = progress.progress || 0;
            let status = progress.status || 'pending';

            // Status messages
            const statusMessages = {
                'pending': 'Waiting in queue...',
                'downloading': 'Downloading...',
                'processing': 'Processing video...',
                'completed': 'Download completed!',
                'failed': 'Download failed',
                'cancelled': 'Download cancelled'
            };

            const statusText = statusMessages[status] || status;

            // Format details
            const details = {};
            if (progress.speed) {
                details.speed = this.formatSpeed(progress.speed);
            }
            if (progress.eta) {
                details.eta = this.formatETA(progress.eta);
            }

            window.ui.updateProgress(percent, statusText, details);

            // Check if download is complete or failed
            if (status === 'completed') {
                this.stopProgressPolling();
                window.ui.showToast('success', 'Download Complete', 'Your video has been downloaded successfully');

                // Reset after 3 seconds
                setTimeout(() => {
                    this.resetDownload();
                }, 3000);
            } else if (status === 'failed') {
                this.stopProgressPolling();
                const errorMsg = progress.error || 'Unknown error';
                window.ui.showToast('error', 'Download Failed', errorMsg);

                // Reset after 3 seconds
                setTimeout(() => {
                    this.resetDownload();
                }, 3000);
            }
        } catch (error) {
            console.error('Failed to get download progress:', error);
            // Don't stop polling on error, just log it
        }
    }

    /**
     * Reset download state
     */
    resetDownload() {
        this.currentDownloadId = null;
        this.currentVideoInfo = null;
        window.ui.resetProgress();

        // Clear form
        const urlInput = document.getElementById('urlInput');
        if (urlInput) {
            urlInput.value = '';
        }

        // Hide video info and format selection
        window.ui.toggleElement('#videoInfo', false);
        window.ui.toggleElement('#formatSelection', false);
    }

    /**
     * Format speed (bytes/sec to human readable)
     * @param {number} bytesPerSecond
     * @returns {string}
     */
    formatSpeed(bytesPerSecond) {
        const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
        let size = bytesPerSecond;
        let unitIndex = 0;

        while (size >= 1024 && unitIndex < units.length - 1) {
            size /= 1024;
            unitIndex++;
        }

        return `${size.toFixed(1)} ${units[unitIndex]}`;
    }

    /**
     * Format ETA (seconds to human readable)
     * @param {number} seconds
     * @returns {string}
     */
    formatETA(seconds) {
        if (seconds < 60) {
            return `${seconds}s`;
        } else if (seconds < 3600) {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${mins}m ${secs}s`;
        } else {
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${mins}m`;
        }
    }
}

// Create global download manager instance
let downloadManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        downloadManager = new DownloadManager();
        window.downloadManager = downloadManager;
    });
} else {
    downloadManager = new DownloadManager();
    window.downloadManager = downloadManager;
}
