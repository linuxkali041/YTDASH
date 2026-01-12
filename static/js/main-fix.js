// Main site fix - Handle logged in/out states properly
console.log('Main site fix loaded');

// Wait for DOM
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded, initializing main site');

    // Hide OAuth-dependent elements
    const authPrompt = document.getElementById('authPromptCard');
    if (authPrompt) {
        authPrompt.remove();
        console.log('Removed auth prompt card');
    }

    // Check if user is logged in
    const accessToken = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isLoggedIn = !!accessToken;

    console.log('Login status:', isLoggedIn, 'User:', user);

    // Add appropriate buttons to header
    const headerContent = document.querySelector('.header-content');
    if (headerContent) {
        // Remove existing auth status
        const authStatus = document.getElementById('authStatus');
        if (authStatus) authStatus.remove();

        // Create auth section
        const authLinks = document.createElement('div');
        authLinks.style.cssText = 'display: flex; gap: 1rem; align-items: center; margin-left: auto;';

        if (isLoggedIn) {
            // User is logged in - show user menu
            authLinks.innerHTML = `
                <span style="color: var(--text-secondary);">Welcome, <strong>${user.username || 'User'}</strong></span>
                ${user.role === 'admin' ?
                    '<a href="/admin" class="btn btn-primary btn-sm" style="text-decoration: none;">Admin Panel</a>' :
                    '<a href="/profile" class="btn btn-primary btn-sm" style="text-decoration: none;">My Profile</a>'
                }
                <button id="logoutBtnMain" class="btn btn-outline btn-sm">Logout</button>
            `;

            // Add logout handler
            setTimeout(() => {
                const logoutBtn = document.getElementById('logoutBtnMain');
                if (logoutBtn) {
                    logoutBtn.addEventListener('click', function () {
                        localStorage.clear();
                        window.location.reload();
                    });
                }
            }, 100);

            console.log('Showing logged-in user menu');
        } else {
            // User is NOT logged in - show login/register
            authLinks.innerHTML = `
                <a href="/login" class="btn btn-primary btn-sm" style="text-decoration: none;">Login</a>
                <a href="/register" class="btn btn-outline btn-sm" style="text-decoration: none;">Register</a>
            `;
            console.log('Showing login/register buttons');
        }

        headerContent.appendChild(authLinks);
    }

    // Handle Get Info button
    const getInfoBtn = document.getElementById('getInfoBtn');
    if (getInfoBtn) {
        getInfoBtn.addEventListener('click', async function (e) {
            e.preventDefault();

            if (!isLoggedIn) {
                if (window.ui) window.ui.showToast('warning', 'Login Required', 'Please login to use the video downloader.');
                else alert('Please login first to use the video downloader.');
                window.location.href = '/login';
                return;
            }

            const urlInput = document.getElementById('urlInput');
            const videoUrl = urlInput.value.trim();

            if (!videoUrl) {
                if (window.ui) window.ui.showToast('info', 'Input Required', 'Please enter a YouTube URL first!');
                else alert('Please enter a YouTube URL first!');
                return;
            }

            // Detect if it's a playlist URL
            // Only treat as playlist if it has 'list=' or '/playlist' AND DOES NOT have 'v=' (which implies a specific video in a playlist)
            const isPlaylist = (videoUrl.includes('list=') || videoUrl.includes('/playlist')) && !videoUrl.includes('v=');

            getInfoBtn.disabled = true;
            getInfoBtn.innerHTML = '<span><i class="fas fa-spinner fa-spin"></i></span><span>Loading...</span>';

            try {
                if (isPlaylist) {
                    // Handle playlist
                    const response = await fetch('/api/playlist/info', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${accessToken}`
                        },
                        body: JSON.stringify({ url: videoUrl })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        window.currentPlaylistData = data; // Store for download

                        // Show playlist info in a custom UI (we'll need to add this to HTML)
                        showPlaylistInfo(data);

                        if (window.ui) window.ui.showToast('success', 'Playlist Found', `${data.video_count} videos found.`);
                    } else {
                        const error = await response.json();
                        if (window.ui) window.ui.showToast('error', 'Error', error.detail || 'Failed to fetch playlist info');
                        else alert('Error: ' + (error.detail || 'Failed to fetch playlist info'));
                    }
                } else {
                    // Handle single video (existing code)
                    const response = await fetch('/api/video/info', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${accessToken}`
                        },
                        body: JSON.stringify({ url: videoUrl })
                    });

                    if (response.ok) {
                        const data = await response.json();

                        document.getElementById('videoTitle').textContent = data.title || 'Unknown Title';
                        document.getElementById('videoMeta').textContent =
                            `Duration: ${data.duration || 'N/A'} | Uploader: ${data.uploader || 'N/A'}`;
                        document.getElementById('videoDescription').textContent =
                            data.description || 'No description available';

                        const thumbnail = document.getElementById('videoThumbnail');
                        if (data.thumbnail) {
                            thumbnail.src = data.thumbnail;
                            thumbnail.classList.remove('hidden');
                        }

                        document.getElementById('videoInfo').classList.remove('hidden');
                        document.getElementById('formatSelection').classList.remove('hidden');

                        if (window.ui) window.ui.showToast('success', 'Video Found', 'Video info loaded successfully.');
                    } else {
                        const error = await response.json();
                        if (window.ui) window.ui.showToast('error', 'Error', error.detail || 'Failed to fetch video info');
                        else alert('Error: ' + (error.detail || 'Failed to fetch video info'));
                    }
                }
            } catch (error) {
                console.error('Error fetching info:', error);
                if (window.ui) window.ui.showToast('error', 'Network Error', 'Please try again.');
                else alert('Network error. Please try again.');
            } finally {
                getInfoBtn.disabled = false;
                getInfoBtn.innerHTML = '<span><i class="fas fa-search"></i></span><span>Get Video Info</span>';
            }
        });
        console.log('Get Info button configured');
    }


    // Handle Download Form - CLIENT-SIDE DOWNLOAD
    const downloadForm = document.getElementById('downloadForm');
    if (downloadForm) {
        downloadForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            if (!isLoggedIn) {
                alert('Please login first.');
                window.location.href = '/login';
                return;
            }

            const urlInput = document.getElementById('urlInput');
            const videoUrl = urlInput.value.trim();
            const formatType = document.getElementById('formatType').value;
            const quality = document.getElementById('quality').value;

            if (!videoUrl) {
                alert('Please enter a URL and get video info first!');
                return;
            }

            const progressSection = document.getElementById('progressSection');
            const progressBar = document.getElementById('progressBar');
            const progressPercent = document.getElementById('progressPercent');
            const progressStatus = document.getElementById('progressStatus');

            progressSection.classList.remove('hidden');
            progressStatus.textContent = 'Preparing download...';
            progressBar.style.width = '10%';
            progressPercent.textContent = '10%';

            try {
                const response = await fetch('/api/video/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${accessToken}`
                    },
                    body: JSON.stringify({
                        url: videoUrl,
                        format_type: formatType,
                        quality: quality
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Download failed');
                }

                const startData = await response.json();
                const downloadId = startData.download_id;

                progressStatus.textContent = 'Queued... Waiting for server to start...';

                // Polling function
                const pollProgress = async () => {
                    try {
                        const progResponse = await fetch(`/api/download/progress/${downloadId}`, {
                            headers: { 'Authorization': `Bearer ${accessToken}` }
                        });

                        if (!progResponse.ok) throw new Error('Failed to check progress');

                        const progData = await progResponse.json();

                        // Update UI
                        const percentage = Math.round(progData.progress || 0);
                        progressBar.style.width = `${percentage}%`;
                        progressPercent.textContent = `${percentage}%`;
                        progressStatus.textContent = `Downloading... ${progData.speed_display || ''} (ETA: ${progData.eta_display || 'calculating...'})`;

                        if (progData.status === 'completed') {
                            progressStatus.textContent = 'Download complete! Saving file...';
                            progressBar.style.width = '100%';

                            // Trigger file download
                            const fileUrl = `/api/download/file/${downloadId}`;
                            window.location.href = fileUrl;

                            setTimeout(() => {
                                alert('✅ Download Complete! File should appear in your downloads.');
                            }, 1000);
                            return; // Stop polling
                        } else if (progData.status === 'failed') {
                            throw new Error(progData.error || 'Download failed on server');
                        } else {
                            // Continue polling
                            setTimeout(pollProgress, 1000);
                        }
                    } catch (err) {
                        console.error('Polling error:', err);
                        progressStatus.textContent = 'Error: ' + err.message;
                        alert('❌ Download failed: ' + err.message);
                    }
                };

                // Start polling
                pollProgress();

            } catch (error) {
                console.error('Initiation error:', error);
                progressStatus.textContent = 'Error: ' + error.message;
                progressBar.style.width = '0%';
                alert('❌ Failed to start download: ' + error.message);
            }
        });

        console.log('Download form configured for CLIENT-SIDE downloads');
    }

    // Settings modal
    const settingsBtn = document.getElementById('settingsBtn');
    const settingsModal = document.getElementById('settingsModal');
    if (settingsBtn && settingsModal) {
        settingsBtn.addEventListener('click', function (e) {
            e.preventDefault();
            settingsModal.classList.add('active');
        });

        const closeBtn = settingsModal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                settingsModal.classList.remove('active');
            });
        }

        settingsModal.addEventListener('click', function (e) {
            if (e.target === settingsModal) {
                settingsModal.classList.remove('active');
            }
        });
    }

    // ============================================
    // Playlist Functions
    // ============================================

    window.showPlaylistInfo = function (playlistData) {
        // Hide single video info
        document.getElementById('videoInfo')?.classList.add('hidden');

        // Create or get playlist info container
        let playlistInfo = document.getElementById('playlistInfo');
        if (!playlistInfo) {
            playlistInfo = document.createElement('div');
            playlistInfo.id = 'playlistInfo';
            playlistInfo.className = 'card';
            playlistInfo.style.marginBottom = '2rem';

            // Insert after videoInfo
            const videoInfo = document.getElementById('videoInfo');
            videoInfo.parentNode.insertBefore(playlistInfo, videoInfo.nextSibling);
        }

        // Build playlist UI
        playlistInfo.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">📋 ${playlistData.title}</h3>
                <p class="card-subtitle">
                    ${playlistData.video_count} videos
                    ${playlistData.uploader ? `• ${playlistData.uploader}` : ''}
                </p>
            </div>
            <div style="margin-bottom: 1rem;">
                <button id="selectAllVideos" class="btn btn-sm btn-outline">Select All</button>
                <button id="deselectAllVideos" class="btn btn-sm btn-outline">Deselect All</button>
            </div>
            <div id="playlistVideos" style="max-height: 400px; overflow-y: auto; margin-bottom: 1rem;">
                ${playlistData.videos.map((video, idx) => `
                    <div class="video-item" style="display: flex; align-items: center; padding: 0.75rem; border-bottom: 1px solid var(--border-color);">
                        <input type="checkbox" id="video-${idx}" value="${video.video_id}" checked style="margin-right: 1rem;">
                        <label for="video-${idx}" style="flex: 1; cursor: pointer;">
                            <strong>${video.title}</strong>
                            ${video.duration ? `<span style="color: var(--text-secondary);"> • ${formatDuration(video.duration)}</span>` : ''}
                        </label>
                    </div>
                `).join('')}
            </div>
        `;

        playlistInfo.classList.remove('hidden');
        document.getElementById('formatSelection').classList.remove('hidden');

        // Add select all/deselect all handlers
        document.getElementById('selectAllVideos').addEventListener('click', () => {
            document.querySelectorAll('#playlistVideos input[type="checkbox"]').forEach(cb => cb.checked = true);
        });

        document.getElementById('deselectAllVideos').addEventListener('click', () => {
            document.querySelectorAll('#playlistVideos input[type="checkbox"]').forEach(cb => cb.checked = false);
        });
    };

    window.formatDuration = function (seconds) {
        if (!seconds) return 'Unknown';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return hours > 0 ? `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}` : `${minutes}:${secs.toString().padStart(2, '0')}`;
    };

    // Update download form to handle playlists
    const originalSubmitHandler = downloadForm.onsubmit;
    downloadForm.addEventListener('submit', async function (e) {
        // Check if we're in playlist mode
        if (window.currentPlaylistData) {
            e.preventDefault();
            e.stopPropagation();

            if (!isLoggedIn) {
                alert('Please login first.');
                window.location.href = '/login';
                return false;
            }

            // Get selected videos
            const selectedVideos = Array.from(document.querySelectorAll('#playlistVideos input[type="checkbox"]:checked'))
                .map(cb => cb.value);

            if (selectedVideos.length === 0) {
                alert('Please select at least one video to download!');
                return false;
            }

            const formatType = document.getElementById('formatType').value;
            const quality = document.getElementById('quality').value;

            // Show progress
            const progressSection = document.getElementById('progressSection');
            const progressBar = document.getElementById('progressBar');
            const progressPercent = document.getElementById('progressPercent');
            const progressStatus = document.getElementById('progressStatus');

            progressSection.classList.remove('hidden');
            progressStatus.textContent = `Downloading ${selectedVideos.length} videos from playlist...`;
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';

            try {
                const response = await fetch('/api/playlist/download', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${accessToken}`
                    },
                    body: JSON.stringify({
                        url: document.getElementById('urlInput').value.trim(),
                        video_ids: selectedVideos.length === window.currentPlaylistData.videos.length ? null : selectedVideos,
                        format_type: formatType,
                        quality: quality
                    })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Playlist download failed');
                }

                const startData = await response.json();
                const playlistId = startData.playlist_id;

                // Create a container for video progress details
                let progressDetails = document.getElementById('playlistProgressDetails');
                if (!progressDetails) {
                    progressDetails = document.createElement('div');
                    progressDetails.id = 'playlistProgressDetails';
                    progressDetails.style.marginTop = '1rem';
                    progressDetails.style.maxHeight = '300px';
                    progressDetails.style.overflowY = 'auto';
                    progressDetails.style.borderTop = '1px solid var(--border-color)';
                    progressDetails.style.paddingTop = '1rem';
                    progressSection.appendChild(progressDetails);
                } else {
                    progressDetails.innerHTML = ''; // Clear previous
                }

                // Poll for playlist progress
                const pollPlaylistProgress = async () => {
                    try {
                        const progResponse = await fetch(`/api/playlist/progress/${playlistId}`, {
                            headers: { 'Authorization': `Bearer ${accessToken}` }
                        });

                        if (!progResponse.ok) throw new Error('Failed to check progress');

                        const progData = await progResponse.json();

                        // Update Aggregate UI
                        const percentage = Math.round(progData.overall_progress || 0);
                        progressBar.style.width = `${percentage}%`;
                        progressPercent.textContent = `${percentage}%`;
                        progressStatus.textContent = `Downloaded ${progData.completed_videos}/${progData.total_videos} • Active: ${progData.downloading_videos} • Failed: ${progData.failed_videos}`;

                        // Update Individual Video Progress
                        if (progData.video_progress && progData.video_progress.length > 0) {
                            // Track auto-downloaded videos
                            if (!window.downloadedVideos) window.downloadedVideos = new Set();

                            progressDetails.innerHTML = progData.video_progress.map(video => {
                                let statusIcon = '⏳';
                                let statusClass = 'text-secondary';
                                let actionHtml = '';

                                if (video.status === 'downloading') {
                                    statusIcon = '⬇️';
                                    statusClass = 'text-primary';
                                } else if (video.status === 'completed' || video.status === 'processing') {
                                    statusIcon = '✅';
                                    statusClass = 'text-success';
                                    actionHtml = `<a href="/api/download/file/${video.download_id}" class="btn btn-xs btn-primary" target="_blank" style="padding: 2px 8px; font-size: 0.8rem;">Download</a>`;

                                    // Auto-download logic
                                    if (!window.downloadedVideos.has(video.download_id)) {
                                        window.downloadedVideos.add(video.download_id);
                                        // Use iframe to trigger download without popup blocking
                                        const iframe = document.createElement('iframe');
                                        iframe.style.display = 'none';
                                        iframe.src = `/api/download/file/${video.download_id}`;
                                        document.body.appendChild(iframe);
                                        // Clean up iframe after a minute
                                        setTimeout(() => document.body.removeChild(iframe), 60000);

                                        // Show toast if available
                                        if (window.ui) window.ui.showToast('success', 'Downloaded', `${video.filename || 'Video'} saved to your device.`);
                                    }
                                } else if (video.status === 'failed') {
                                    statusIcon = '❌';
                                    statusClass = 'text-danger';
                                    actionHtml = `<span class="text-danger" title="${video.error || 'Failed'}">Failed</span>`;
                                }

                                const vidPercent = Math.round(video.progress || 0);

                                return `
                                    <div class="video-progress-item" style="display: flex; align-items: center; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px solid var(--border-color); font-size: 0.9rem;">
                                        <div style="flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; margin-right: 1rem; display: flex; align-items: center;">
                                            <span class="${statusClass}" style="margin-right: 0.5rem; min-width: 20px;">${statusIcon}</span>
                                            <span style="font-weight: 500;" title="${video.filename || 'Waiting...'}">${video.filename || 'Waiting...'}</span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 10px;">
                                            <span style="min-width: 35px; text-align: right; font-size: 0.85rem; color: var(--text-secondary);">${vidPercent}%</span>
                                            ${actionHtml}
                                        </div>
                                    </div>
                                `;
                            }).join('');
                        }

                        if (progData.completed_videos + progData.failed_videos >= progData.total_videos) {
                            progressStatus.textContent = `✅ Playlist download complete! ${progData.completed_videos} successful, ${progData.failed_videos} failed.`;
                            progressBar.style.width = '100%';

                            if (window.ui) window.ui.showToast('success', 'Complete', `Playlist downloaded: ${progData.completed_videos}/${progData.total_videos} videos`);
                            return; // Stop polling
                        } else {
                            setTimeout(pollPlaylistProgress, 2000); // Poll every 2 seconds
                        }
                    } catch (err) {
                        console.error('Polling error:', err);
                        progressStatus.textContent = 'Error: ' + err.message;
                    }
                };

                pollPlaylistProgress();

            } catch (error) {
                console.error('Playlist download error:', error);
                progressStatus.textContent = 'Error: ' + error.message;
                progressBar.style.width = '0%';
                alert('❌ Failed to start playlist download: ' + error.message);
            }

            return false;
        }
    }, true); // Use capture to run before original handler

    console.log('Main site initialization complete - CLIENT-SIDE DOWNLOADS ENABLED');
});
