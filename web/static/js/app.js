// KitchenRadio Web Interface JavaScript

class KitchenRadioApp {
    constructor() {
        this.statusUpdateInterval = null;
        this.mpdState = 'unknown';
        this.librespotState = 'unknown';
        this.selectedPlaylist = '';
        this.currentSource = null;
        this.availableSources = [];
        
        this.init();
    }
    
    init() {
        // Start periodic status updates
        this.startStatusUpdates();
        
        // Initial status fetch
        this.refreshStatus();
        
        // Load playlists
        this.loadPlaylists();
        
        console.log('KitchenRadio Web Interface initialized');
    }
    
    startStatusUpdates() {
        // Update status every 2 seconds
        this.statusUpdateInterval = setInterval(() => {
            this.refreshStatus();
        }, 2000);
    }
    
    stopStatusUpdates() {
        if (this.statusUpdateInterval) {
            clearInterval(this.statusUpdateInterval);
            this.statusUpdateInterval = null;
        }
    }
    
    async refreshStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const status = await response.json();
                this.updateUI(status);
                this.updateLastUpdate();
            } else {
                this.showError('Failed to get status');
                this.updateDaemonStatus('disconnected');
            }
        } catch (error) {
            console.error('Status fetch error:', error);
            this.showError('Connection error');
            this.updateDaemonStatus('disconnected');
        }
    }
    
    updateUI(status) {
        // Update daemon status
        this.updateDaemonStatus(status.daemon_running ? 'connected' : 'disconnected');
        
        // Update source selector
        this.updateSourceSelector(status.current_source, status.available_sources || []);
        
        // Update MPD panel
        this.updateMPDPanel(status.mpd || {});
        
        // Update Librespot panel
        this.updateLibrespotPanel(status.librespot || {});
    }
    
    updateDaemonStatus(status) {
        const statusElement = document.getElementById('daemon-status');
        statusElement.className = `status-indicator ${status}`;
        
        const statusText = {
            'connected': 'Connected',
            'disconnected': 'Disconnected',
            'connecting': 'Connecting...'
        };
        
        statusElement.innerHTML = `<i class="fas fa-circle"></i> ${statusText[status] || status}`;
    }
    
    updateMPDPanel(mpdStatus) {
        const panel = document.getElementById('mpd-panel');
        const statusElement = document.getElementById('mpd-status');
        const currentElement = document.getElementById('mpd-current');
        const stateElement = document.getElementById('mpd-state');
        const volumeSlider = document.getElementById('mpd-volume');
        const volumeText = document.getElementById('mpd-volume-text');
        const playPauseBtn = document.getElementById('mpd-play-pause');
        
        const connected = mpdStatus.connected || false;
        
        // Update connection status
        statusElement.className = `backend-status ${connected ? 'connected' : 'disconnected'}`;
        statusElement.innerHTML = `<i class="fas fa-circle"></i> ${connected ? 'Connected' : 'Disconnected'}`;
        
        // Enable/disable panel
        panel.className = `backend-panel ${connected ? '' : 'disabled'}`;
        
        if (connected) {
            // Update current track
            this.updateCurrentTrack(currentElement, mpdStatus.current_song);
            
            // Update state
            this.mpdState = mpdStatus.state || 'unknown';
            stateElement.textContent = this.mpdState;
            
            // Update play/pause button
            const isPlaying = this.mpdState === 'play';
            playPauseBtn.innerHTML = `<i class="fas fa-${isPlaying ? 'pause' : 'play'}"></i>`;
            
            // Update volume
            if (mpdStatus.volume !== undefined) {
                volumeSlider.value = mpdStatus.volume;
                volumeText.textContent = `${mpdStatus.volume}%`;
            }
        } else {
            // Reset display
            currentElement.querySelector('.track-info').innerHTML = `
                <div class="title">Not connected</div>
                <div class="artist"></div>
                <div class="album"></div>
            `;
            stateElement.textContent = 'Disconnected';
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    
    updateLibrespotPanel(librespotStatus) {
        const panel = document.getElementById('librespot-panel');
        const statusElement = document.getElementById('librespot-status');
        const currentElement = document.getElementById('librespot-current');
        const stateElement = document.getElementById('librespot-state');
        const volumeSlider = document.getElementById('librespot-volume');
        const volumeText = document.getElementById('librespot-volume-text');
        const playPauseBtn = document.getElementById('librespot-play-pause');
        
        const connected = librespotStatus.connected || false;
        
        // Update connection status
        statusElement.className = `backend-status ${connected ? 'connected' : 'disconnected'}`;
        statusElement.innerHTML = `<i class="fas fa-circle"></i> ${connected ? 'Connected' : 'Disconnected'}`;
        
        // Enable/disable panel
        panel.className = `backend-panel ${connected ? '' : 'disabled'}`;
        
        if (connected) {
            // Update current track
            this.updateCurrentTrack(currentElement, librespotStatus.current_track);
            
            // Update state
            this.librespotState = librespotStatus.state || 'unknown';
            stateElement.textContent = this.librespotState;
            
            // Update play/pause button
            const isPlaying = this.librespotState === 'Playing';
            playPauseBtn.innerHTML = `<i class="fas fa-${isPlaying ? 'pause' : 'play'}"></i>`;
            
            // Update volume
            if (librespotStatus.volume !== undefined) {
                volumeSlider.value = librespotStatus.volume;
                volumeText.textContent = `${librespotStatus.volume}%`;
            }
        } else {
            // Reset display
            currentElement.querySelector('.track-info').innerHTML = `
                <div class="title">Not connected</div>
                <div class="artist"></div>
                <div class="album"></div>
            `;
            stateElement.textContent = 'Disconnected';
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
    }
    
    updateCurrentTrack(element, track) {
        const trackInfo = element.querySelector('.track-info');
        
        if (track && track.title) {
            trackInfo.innerHTML = `
                <div class="title">${this.escapeHtml(track.title)}</div>
                <div class="artist">${this.escapeHtml(track.artist || 'Unknown Artist')}</div>
                <div class="album">${this.escapeHtml(track.album || '')}</div>
            `;
        } else {
            trackInfo.innerHTML = `
                <div class="title">No track playing</div>
                <div class="artist"></div>
                <div class="album"></div>
            `;
        }
    }
    
    updateSourceSelector(currentSource, availableSources) {
        this.currentSource = currentSource;
        this.availableSources = availableSources;
        
        const selector = document.getElementById('source-select');
        const currentValue = selector.value;
        
        // Clear and rebuild options
        selector.innerHTML = '<option value="">-- No Source --</option>';
        
        // Add available sources
        availableSources.forEach(source => {
            const option = document.createElement('option');
            if (source === 'mpd') {
                option.value = 'mpd';
                option.textContent = 'MPD Player';
            } else if (source === 'librespot' || source === 'spotify') {
                option.value = 'spotify';
                option.textContent = 'Spotify';
            }
            selector.appendChild(option);
        });
        
        // Set current selection
        if (currentSource) {
            const sourceValue = currentSource === 'librespot' ? 'spotify' : currentSource;
            selector.value = sourceValue;
        } else {
            selector.value = '';
        }
        
        // Enable/disable selector
        selector.disabled = availableSources.length === 0;
    }
    
    async setSource(source) {
        if (!source) {
            this.showError('Please select a source');
            return false;
        }
        
        try {
            const response = await fetch(`/api/source/${source}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showSuccess(`Source set to ${source.toUpperCase()}`);
                // Refresh status to update UI
                setTimeout(() => this.refreshStatus(), 500);
                return true;
            } else {
                this.showError(result.error || 'Failed to set source');
                return false;
            }
        } catch (error) {
            console.error('Set source error:', error);
            this.showError('Network error');
            return false;
        }
    }
    
    updateLastUpdate() {
        const lastUpdateElement = document.getElementById('last-update');
        const now = new Date();
        lastUpdateElement.textContent = `Last update: ${now.toLocaleTimeString()}`;
    }
    
    async sendControlCommand(backend, action, data = null) {
        try {
            const response = await fetch(`/api/${backend}/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: data ? JSON.stringify(data) : null
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Command successful - status will be updated on next refresh
                return true;
            } else {
                this.showError(result.error || 'Command failed');
                return false;
            }
        } catch (error) {
            console.error('Control command error:', error);
            this.showError('Network error');
            return false;
        }
    }
    
    async sendVolumeCommand(backend, action) {
        try {
            const response = await fetch(`/api/volume/${backend}/${action}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                // Update volume display immediately
                const slider = document.getElementById(`${backend}-volume`);
                const text = document.getElementById(`${backend}-volume-text`);
                if (result.volume !== undefined) {
                    slider.value = result.volume;
                    text.textContent = `${result.volume}%`;
                }
                return true;
            } else {
                this.showError(result.error || 'Volume command failed');
                return false;
            }
        } catch (error) {
            console.error('Volume command error:', error);
            this.showError('Network error');
            return false;
        }
    }
    
    async loadPlaylists() {
        try {
            const response = await fetch('/api/mpd/playlists');
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.playlists) {
                    this.updatePlaylistSelector(result.playlists);
                } else {
                    console.error('Failed to load playlists:', result.error);
                }
            } else {
                console.error('Failed to fetch playlists');
            }
        } catch (error) {
            console.error('Playlist fetch error:', error);
        }
    }
    
    updatePlaylistSelector(playlists) {
        const selector = document.getElementById('mpd-playlist-select');
        
        // Clear existing options except the first one
        selector.innerHTML = '<option value="">-- Select Playlist --</option>';
        
        // Add playlist options
        playlists.forEach(playlist => {
            const option = document.createElement('option');
            option.value = playlist;
            option.textContent = playlist;
            selector.appendChild(option);
        });
        
        console.log(`Loaded ${playlists.length} playlists`);
    }
    
    async loadSelectedPlaylist() {
        const selector = document.getElementById('mpd-playlist-select');
        const playlistName = selector.value;
        
        if (!playlistName) {
            this.showError('Please select a playlist');
            return false;
        }
        
        try {
            const response = await fetch('/api/mpd/load_playlist', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ playlist: playlistName })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showSuccess(`Loaded playlist: ${playlistName}`);
                // Refresh status to update current track display
                setTimeout(() => this.refreshStatus(), 500);
                return true;
            } else {
                this.showError(result.error || 'Failed to load playlist');
                return false;
            }
        } catch (error) {
            console.error('Load playlist error:', error);
            this.showError('Network error');
            return false;
        }
    }
    
    showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type} show`;
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }
    
    showError(message) {
        this.showToast(message, 'error');
    }
    
    showSuccess(message) {
        this.showToast(message, 'success');
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global app instance
let app;

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    app = new KitchenRadioApp();
});

// Global control functions for buttons

// Source Controls
function sourceChanged() {
    const selector = document.getElementById('source-select');
    const selectedSource = selector.value;
    
    if (selectedSource && selectedSource !== app.currentSource) {
        app.setSource(selectedSource);
    }
}

// MPD Controls
function mpdControl(action) {
    app.sendControlCommand('mpd', action);
}

function mpdPlayPause() {
    const action = app.mpdState === 'play' ? 'pause' : 'play';
    app.sendControlCommand('mpd', action);
}

function mpdSetVolume(volume) {
    app.sendControlCommand('mpd', 'volume', { level: parseInt(volume) });
    document.getElementById('mpd-volume-text').textContent = `${volume}%`;
}

function mpdVolumeControl(action) {
    app.sendVolumeCommand('mpd', action);
}

// Librespot Controls
function librespotControl(action) {
    app.sendControlCommand('librespot', action);
}

function librespotPlayPause() {
    const action = app.librespotState === 'Playing' ? 'pause' : 'play';
    app.sendControlCommand('librespot', action);
}

function librespotSetVolume(volume) {
    app.sendControlCommand('librespot', 'volume', { level: parseInt(volume) });
    document.getElementById('librespot-volume-text').textContent = `${volume}%`;
}

function librespotVolumeControl(action) {
    app.sendVolumeCommand('librespot', action);
}

// Playlist Controls
function mpdPlaylistChanged() {
    // This function is called when playlist selection changes
    // Could be used for preview or other functionality
    const selector = document.getElementById('mpd-playlist-select');
    app.selectedPlaylist = selector.value;
}

function mpdLoadPlaylist() {
    app.loadSelectedPlaylist();
}

function mpdRefreshPlaylists() {
    app.loadPlaylists();
}

// General Controls
function refreshStatus() {
    app.refreshStatus();
}

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        app.stopStatusUpdates();
    } else {
        app.startStatusUpdates();
        app.refreshStatus();
    }
});
