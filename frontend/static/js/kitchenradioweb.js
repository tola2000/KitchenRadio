// Simple client for KitchenRadio web UI
(() => {
  const statusUrl = '/api/status';
  const displayUrl = '/api/display'; // expects JSON { data: "data:image/png;base64,..." } or direct image
  const controlUrl = '/api/control'; // POST { action: 'play'|'pause'|'next'|'prev'|'volume', ... }
  const menuSelectUrl = '/api/menu_select'; // POST {index: N}

  const pollIntervalMs = 2000;
  const displayPollMs = 500;

  let displayTimer = null;
  let statusTimer = null;

  const els = {
    statusText: document.getElementById('statusText'),
    sourceLabel: document.getElementById('sourceLabel'),
    trackTitle: document.getElementById('trackTitle'),
    trackArtist: document.getElementById('trackArtist'),
    volumeSlider: document.getElementById('volumeSlider'),
    btnPrev: document.getElementById('btnPrev'),
    btnPlay: document.getElementById('btnPlay'),
    btnNext: document.getElementById('btnNext'),
    btnMenu: document.getElementById('btnMenu'),
    deviceDisplay: document.getElementById('deviceDisplay'),
    menuTitle: document.getElementById('menuTitle'),
    menuList: document.getElementById('menuList'),
  };

  async function fetchJson(url, opts = {}) {
    try {
      const res = await fetch(url, opts);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (e) {
      console.debug('fetch error', url, e);
      return null;
    }
  }

  async function refreshStatus() {
    const data = await fetchJson(statusUrl);
    if (!data) {
      els.statusText.textContent = 'Offline';
      return;
    }
    els.statusText.textContent = data.daemon_running ? 'Running' : 'Stopped';
    els.sourceLabel.textContent = (data.mpd && data.mpd.connected && data.mpd.state) ? `MPD (${data.mpd.state})` : (data.librespot && data.librespot.connected ? `Spotify (${data.librespot.state})` : '—');

    const track = (data.mpd && data.mpd.current_song) || (data.librespot && data.librespot.current_track);
    if (track && track.title) {
      els.trackTitle.textContent = track.title;
      els.trackArtist.textContent = track.artist || '';
    } else {
      els.trackTitle.textContent = 'No track';
      els.trackArtist.textContent = '';
    }

    const vol = (data.mpd && data.mpd.volume) || (data.librespot && data.librespot.volume);
    if (vol !== undefined && vol !== null) {
      els.volumeSlider.value = Number(vol);
    }
  }

  async function refreshDisplay() {
    try {
      const res = await fetch(displayUrl);
      if (!res.ok) return;
      // support image or JSON with data
      const ctype = res.headers.get('content-type') || '';
      if (ctype.startsWith('application/json')) {
        const json = await res.json();
        if (json && json.data) els.deviceDisplay.src = json.data;
      } else {
        // binary image — convert to blob url
        const blob = await res.blob();
        els.deviceDisplay.src = URL.createObjectURL(blob);
      }
    } catch (e) {
      console.debug('display fetch error', e);
    }
  }

  async function postControl(action, body = {}) {
    try {
      await fetch(controlUrl, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action, ...body })});
    } catch (e) { console.debug('control post fail', e); }
  }

  // UI wiring
  els.btnPlay.addEventListener('click', () => postControl('playpause'));
  els.btnNext.addEventListener('click', () => postControl('next'));
  els.btnPrev.addEventListener('click', () => postControl('previous'));
  els.volumeSlider.addEventListener('change', (e) => postControl('volume', { volume: Number(e.target.value) }));

  // Menu handling
  const menuModal = new bootstrap.Modal(document.getElementById('menuModal'));
  els.btnMenu.addEventListener('click', async () => {
    // ask backend for current menu (assumes /api/menu returns { title, items: [] })
    const menu = await fetchJson('/api/menu');
    if (!menu) return;
    els.menuTitle.textContent = menu.title || 'Menu';
    els.menuList.innerHTML = '';
    (menu.items || []).forEach((it, idx) => {
      const li = document.createElement('li');
      li.className = 'list-group-item';
      li.textContent = it;
      li.addEventListener('click', async () => {
        await fetch(menuSelectUrl, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ index: idx }) });
        menuModal.hide();
      });
      els.menuList.appendChild(li);
    });
    menuModal.show();
  });

  function startPolling() {
    if (!statusTimer) {
      refreshStatus();
      statusTimer = setInterval(refreshStatus, pollIntervalMs);
    }
    if (!displayTimer) {
      refreshDisplay();
      displayTimer = setInterval(refreshDisplay, displayPollMs);
    }
  }
  function stopPolling() {
    if (statusTimer) clearInterval(statusTimer), statusTimer = null;
    if (displayTimer) clearInterval(displayTimer), displayTimer = null;
  }

  // start
  startPolling();

  // expose for console
  window.kitchenRadioWeb = { refreshStatus, refreshDisplay, stopPolling, startPolling };
})();