// Physical Radio Interface JavaScript

class PhysicalRadioApp {
    constructor() {
        this.statusUpdateInterval = null;
        this.currentSource = null;
        this.availableSources = [];
        this.isPlaying = false;
        this.currentVolume = 0;
        this.menuVisible = false;
        this.currentMenuOptions = [];
        this.currentMenuData = null;
        this.selectedMenuIndex = 0;
        
        this.init();
    }
    
    init() {
        console.log('Physical Radio Interface initialized');
        
        // Start status updates
        this.startStatusUpdates();
        
        // Initial status fetch
        this.refreshStatus();
        
        // Set initial display
        this.updateDisplay();
    }
    
    startStatusUpdates() {
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
                this.updateFromStatus(status);
                this.updateDaemonStatus('connected');
            } else {
                this.showError('Failed to get status');
                this.updateDaemonStatus('disconnected');
            }
        } catch (error) {
            console.error('Status fetch error:', error);
            this.updateDaemonStatus('disconnected');
        }
    }
    
    updateFromStatus(status) {
        // Update current source
        this.currentSource = status.current_source;
        this.availableSources = status.available_sources || [];
        
        // Update source buttons
        this.updateSourceButtons();
        
        // Update playback info
        this.updatePlaybackInfo(status);
        
        // Update volume
        this.updateVolumeDisplay(status);
        
        // Update OLED display
        this.updateDisplay();
    }
    
    updateSourceButtons() {
        // Reset all source buttons
        document.querySelectorAll('.source-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Activate current source button
        if (this.currentSource) {
            const sourceBtn = document.getElementById(`btn-source-${this.currentSource === 'librespot' ? 'spotify' : this.currentSource}`);
            if (sourceBtn) {
                sourceBtn.classList.add('active');
            }
        } else {
            document.getElementById('btn-source-off').classList.add('active');
        }
        
        // Update source indicator in display
        const sourceIndicator = document.getElementById('source-indicator');
        if (this.currentSource) {
            const sourceText = this.currentSource === 'librespot' ? 'SPOTIFY' : this.currentSource.toUpperCase();
            sourceIndicator.innerHTML = `<i class="fas fa-${this.currentSource === 'librespot' ? 'spotify' : 'music'}"></i><span>${sourceText}</span>`;
        } else {
            sourceIndicator.innerHTML = '<i class="fas fa-power-off"></i><span>OFF</span>';
        }
    }
    
    updatePlaybackInfo(status) {
        // Determine if playing from either source
        let isPlaying = false;
        let currentTrack = null;
        
        if (status.mpd && status.mpd.connected && status.mpd.state === 'play') {
            isPlaying = true;
            currentTrack = status.mpd.current_song;
        } else if (status.librespot && status.librespot.connected && status.librespot.state === 'playing') {
            isPlaying = true;
            currentTrack = status.librespot.current_track;
        }
        
        this.isPlaying = isPlaying;
        
        // Update transport buttons
        this.updateTransportButtons(isPlaying);
        
        // Update track info in display
        this.updateTrackDisplay(currentTrack);
        
        // Update playback status
        const playbackStatus = document.getElementById('playback-status');
        if (isPlaying) {
            playbackStatus.innerHTML = '<i class="fas fa-play"></i><span>PLAY</span>';
        } else {
            playbackStatus.innerHTML = '<i class="fas fa-stop"></i><span>STOP</span>';
        }
    }
    
    updateTransportButtons(isPlaying) {
        const hasActiveSource = this.currentSource && this.availableSources.includes(this.currentSource);
        
        // Enable/disable transport buttons based on active source
        document.querySelectorAll('.transport-btn').forEach(btn => {
            btn.disabled = !hasActiveSource;
        });
        
        // Update play button
        const playBtn = document.getElementById('btn-play');
        if (isPlaying) {
            playBtn.classList.add('playing');
            playBtn.innerHTML = '<i class="fas fa-pause"></i><span>PAUSE</span>';
        } else {
            playBtn.classList.remove('playing');
            playBtn.innerHTML = '<i class="fas fa-play"></i><span>PLAY</span>';
        }
    }
    
    updateTrackDisplay(track) {
        const titleEl = document.getElementById('track-title');
        const artistEl = document.getElementById('track-artist');
        const albumEl = document.getElementById('track-album');
        
        if (track) {
            titleEl.textContent = track.title || track.name || 'Unknown Track';
            artistEl.textContent = track.artist || 'Unknown Artist';
            albumEl.textContent = track.album || 'Unknown Album';
        } else if (this.currentSource) {
            titleEl.textContent = 'Ready to Play';
            artistEl.textContent = this.currentSource === 'librespot' ? 'Spotify Connected' : 'MPD Connected';
            albumEl.textContent = 'Select music to start';
        } else {
            titleEl.textContent = 'KitchenRadio';
            artistEl.textContent = 'Ready to Play';
            albumEl.textContent = 'Select a Source';
        }
    }
    
    updateVolumeDisplay(status) {
        let volume = 0;
        
        // Get volume from active source
        if (status.mpd && status.mpd.connected && this.currentSource === 'mpd') {
            volume = status.mpd.volume || 0;
        } else if (status.librespot && status.librespot.connected && this.currentSource === 'librespot') {
            volume = status.librespot.volume || 0;
        }
        
        this.currentVolume = volume;
        
        // Update volume display
        document.getElementById('volume-level').textContent = volume + '%';
        document.getElementById('volume-fill').style.width = volume + '%';
        
        // Enable/disable volume buttons
        const hasActiveSource = this.currentSource && this.availableSources.includes(this.currentSource);
        document.querySelectorAll('.volume-btn').forEach(btn => {
            btn.disabled = !hasActiveSource;
        });
    }
    
    updateDaemonStatus(status) {
        const statusEl = document.getElementById('daemon-status');
        statusEl.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'connected':
                statusEl.innerHTML = '<i class="fas fa-circle"></i>';
                break;
            case 'disconnected':
                statusEl.innerHTML = '<i class="fas fa-times-circle"></i>';
                break;
            case 'connecting':
                statusEl.innerHTML = '<i class="fas fa-circle"></i>';
                break;
        }
    }
    
    updateDisplay() {
        if (this.menuVisible) {
            this.updateMenuDisplay();
        } else {
            document.getElementById('menu-overlay').style.display = 'none';
        }
    }
    
    updateMenuDisplay() {
        const menuOverlay = document.getElementById('menu-overlay');
        const menuTitle = document.getElementById('menu-title');
        const menuOptions = document.getElementById('menu-options');
        
        menuOverlay.style.display = 'block';
        
        if (this.currentMenuOptions.length > 0) {
            // Extract menu type from the menu data structure
            let menuType = 'Menu';
            if (this.currentMenuData && this.currentMenuData.menu_type) {
                menuType = this.currentMenuData.menu_type.replace('_', ' ');
            } else {
                // Determine menu type from source
                if (this.currentSource === 'mpd') {
                    menuType = 'Playlists';
                } else if (this.currentSource === 'librespot' || this.currentSource === 'spotify') {
                    menuType = 'Playback Options';
                }
            }
            
            menuTitle.textContent = menuType.toUpperCase();
            
            // Show current selection and total
            let optionsHtml = `<div class="menu-status">${this.selectedMenuIndex + 1}/${this.currentMenuOptions.length}</div>`;
            
            // Show only the current option (like a real radio display)
            if (this.selectedMenuIndex < this.currentMenuOptions.length) {
                const option = this.currentMenuOptions[this.selectedMenuIndex];
                let label = option.label;
                
                // Add state indicators for toggle options
                if (option.type === 'toggle' && option.state !== undefined) {
                    label += option.state ? ' [ON]' : ' [OFF]';
                }
                
                optionsHtml += `<div class="menu-current-option">${label}</div>`;
                
                // Show navigation hints
                optionsHtml += '<div class="menu-nav-hints">';
                if (this.currentMenuOptions.length > 1) {
                    optionsHtml += '↑↓ Navigate  ';
                }
                optionsHtml += 'OK Select  X Exit</div>';
            }
            
            menuOptions.innerHTML = optionsHtml;
        } else {
            menuTitle.textContent = 'NO MENU';
            menuOptions.innerHTML = '<div class="menu-option">No options available</div>';
        }
    }
    
    showMessage(message, type = 'info') {
        const statusMessages = document.getElementById('status-messages');
        const messageEl = document.createElement('div');
        messageEl.className = `status-message ${type}`;
        messageEl.textContent = message;
        
        statusMessages.appendChild(messageEl);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 3000);
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
}

// Global app instance
let radioApp;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    radioApp = new PhysicalRadioApp();
});

// Source selection functions
async function selectSource(source) {
    if (!radioApp) return;
    
    // If clicking the same source that's already active, show menu
    if (source === radioApp.currentSource && source !== '') {
        await showSourceMenu();
        return;
    }
    
    try {
        radioApp.updateDaemonStatus('connecting');
        
        let response;
        if (source === '') {
            // Turn off - clear source
            response = await fetch('/api/source', {
                method: 'DELETE'
            });
        } else {
            // Set new source
            response = await fetch(`/api/source/${source}`, {
                method: 'POST'
            });
        }
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            radioApp.showSuccess(result.message || `Source set to ${source.toUpperCase()}`);
            // Refresh status immediately
            setTimeout(() => radioApp.refreshStatus(), 500);
        } else {
            radioApp.showError(result.error || 'Failed to set source');
            radioApp.updateDaemonStatus('disconnected');
        }
    } catch (error) {
        console.error('Error setting source:', error);
        radioApp.showError('Connection error');
    }
}

// Show source-specific menu
async function showSourceMenu() {
    if (!radioApp || !radioApp.currentSource) return;
    
    try {
        const response = await fetch('/api/menu');
        if (response.ok) {
            const menuData = await response.json();
            if (menuData.has_menu) {
                radioApp.currentMenuData = menuData;
                radioApp.currentMenuOptions = menuData.options;
                radioApp.selectedMenuIndex = 0;
                radioApp.menuVisible = true;
                radioApp.updateDisplay();
            } else {
                radioApp.showMessage(menuData.message || 'No menu available');
            }
        } else {
            radioApp.showError('Failed to get menu');
        }
    } catch (error) {
        console.error('Error getting menu:', error);
        radioApp.showError('Connection error');
    }
}

// Transport control functions
async function sendCommand(action) {
    if (!radioApp) return;
    
    if (!radioApp.currentSource) {
        radioApp.showError('Please select a source first');
        return;
    }
    
    try {
        const response = await fetch(`/api/control/${action}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            radioApp.showSuccess(result.message || `${action.toUpperCase()} command sent`);
            // Refresh status immediately
            setTimeout(() => radioApp.refreshStatus(), 300);
        } else {
            radioApp.showError(result.error || 'Command failed');
        }
    } catch (error) {
        console.error('Error sending command:', error);
        radioApp.showError('Connection error');
    }
}

// Volume control functions
async function adjustVolume(direction) {
    if (!radioApp) return;
    
    if (!radioApp.currentSource) {
        radioApp.showError('Please select a source first');
        return;
    }
    
    try {
        const response = await fetch(`/api/volume/${direction}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ step: 5 })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // Update volume display immediately
            if (result.volume !== undefined) {
                radioApp.currentVolume = result.volume;
                document.getElementById('volume-level').textContent = result.volume + '%';
                document.getElementById('volume-fill').style.width = result.volume + '%';
            }
            
            radioApp.showSuccess(result.message || `Volume ${direction}`);
        } else {
            radioApp.showError(result.error || 'Volume control failed');
        }
    } catch (error) {
        console.error('Error adjusting volume:', error);
        radioApp.showError('Connection error');
    }
}

// Menu functions
function menuAction(buttonNumber) {
    if (!radioApp) return;
    
    switch (buttonNumber) {
        case 1: // Up
            if (radioApp.menuVisible && radioApp.currentMenuOptions.length > 1) {
                radioApp.selectedMenuIndex = Math.max(0, radioApp.selectedMenuIndex - 1);
                radioApp.updateDisplay();
            }
            break;
        case 2: // Menu - Toggle menu visibility
            if (radioApp.menuVisible) {
                hideMenu();
            } else {
                showSourceMenu();
            }
            break;
        case 3: // Down
            if (radioApp.menuVisible && radioApp.currentMenuOptions.length > 1) {
                radioApp.selectedMenuIndex = Math.min(radioApp.currentMenuOptions.length - 1, radioApp.selectedMenuIndex + 1);
                radioApp.updateDisplay();
            }
            break;
        case 4: // Settings (could be used for additional functions)
            if (radioApp.menuVisible) {
                // Could be used for secondary functions
            }
            break;
        case 5: // Confirm/OK
            if (radioApp.menuVisible) {
                executeMenuOption();
            }
            break;
        case 6: // Cancel/Exit
            if (radioApp.menuVisible) {
                hideMenu();
            }
            break;
    }
}

async function executeMenuOption() {
    if (!radioApp || !radioApp.menuVisible || radioApp.currentMenuOptions.length === 0) return;
    
    const selectedOption = radioApp.currentMenuOptions[radioApp.selectedMenuIndex];
    if (!selectedOption) return;
    
    try {
        const response = await fetch('/api/menu/action', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                action: selectedOption.action,
                option_id: selectedOption.id
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            radioApp.showSuccess(result.message || 'Action executed');
            hideMenu();
            // Refresh status after action
            setTimeout(() => radioApp.refreshStatus(), 500);
        } else {
            radioApp.showError(result.error || 'Action failed');
        }
    } catch (error) {
        console.error('Error executing menu action:', error);
        radioApp.showError('Connection error');
    }
}

function hideMenu() {
    if (!radioApp) return;
    
    radioApp.menuVisible = false;
    radioApp.currentMenuOptions = [];
    radioApp.currentMenuData = null;
    radioApp.selectedMenuIndex = 0;
    radioApp.updateDisplay();
}
