#!/usr/bin/python

import time
import argparse
import json
from mopidy_json_client import MopidyClient

def main():
    parser = argparse.ArgumentParser(description='Diagnose Mopidy connection and events')
    parser.add_argument('--host', '-H', default='localhost', help='Mopidy host')
    parser.add_argument('--port', '-p', type=int, default=6680, help='Mopidy port')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug')
    
    args = parser.parse_args()
    
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'🔌 Connecting to {ws_url}')
    
    # Event counter
    event_count = 0
    
    def count_events(**kwargs):
        nonlocal event_count
        event_count += 1
        print(f'📡 Event #{event_count}: {kwargs}')
    
    # Connection status handler
    def on_connection(is_connected):
        status = "✅ CONNECTED" if is_connected else "❌ DISCONNECTED"
        print(f'🔗 Connection status: {status}')
    
    def on_error(error):
        print(f'❌ Error: {error}')
    
    # Create client with handlers
    mopidy = MopidyClient(
        ws_url=ws_url, 
        debug=args.debug,
        connection_handler=on_connection,
        error_handler=on_error,
        autoconnect=True
    )
    
    if not mopidy.connect(wait_secs=5):
        print('❌ Failed to connect!')
        return
    
    print('✅ WebSocket connected!')
    
    # Bind to ALL possible events
    events_to_monitor = [
        'track_playback_started',
        'track_playback_paused', 
        'track_playback_resumed',
        'track_playback_ended',
        'playback_state_changed',
        'volume_changed',
        'mute_changed',
        'options_changed',
        'tracklist_changed',
        'playlists_loaded',
        'stream_title_changed'
    ]
    
    print('🎧 Binding to events...')
    for event in events_to_monitor:
        try:
            mopidy.bind_event(event, count_events)
            print(f'  ✓ {event}')
        except Exception as e:
            print(f'  ❌ {event}: {e}')
    
    print('\n🔍 DIAGNOSTIC TESTS')
    print('=' * 40)
    
    # Test 1: Basic core methods
    print('📋 Test 1: Core version...')
    try:
        version = mopidy.core.get_version(timeout=2)
        print(f'  ✅ Mopidy version: {version}')
    except Exception as e:
        print(f'  ❌ Core version failed: {type(e).__name__}')
    
    # Test 2: Core describe
    print('📋 Test 2: Core describe...')
    try:
        description = mopidy.core.describe(timeout=2)
        if description:
            print(f'  ✅ Got API description ({len(description)} methods)')
        else:
            print('  ⚠️ Empty description')
    except Exception as e:
        print(f'  ❌ Core describe failed: {type(e).__name__}')
    
    # Test 3: Send raw command
    print('📋 Test 3: Raw command test...')
    try:
        # Send a simple ping-like command
        result = mopidy.core.send('get_version', timeout=2)
        print(f'  ✅ Raw command works: {result}')
    except Exception as e:
        print(f'  ❌ Raw command failed: {type(e).__name__}')
    
    print('\n' + '=' * 50)
    print('🎵 EVENT MONITORING ACTIVE')
    print(f'📡 Watching for events on {len(events_to_monitor)} event types...')
    print('💡 Try these actions in Mopidy:')
    print('  - Open Mopidy web interface')
    print('  - Change any setting')
    print('  - Start/stop music')
    print('  - Change volume')
    print('Press Ctrl+C to stop.')
    print('=' * 50)
    
    try:
        start_time = time.time()
        while True:
            elapsed = int(time.time() - start_time)
            print(f'\r⏱️ Running for {elapsed}s, events received: {event_count}', end='', flush=True)
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print(f'\n\n📊 SUMMARY:')
        print(f'⏱️ Total runtime: {int(time.time() - start_time)}s')
        print(f'📡 Events received: {event_count}')
        if event_count == 0:
            print('⚠️ No events received - possible issues:')
            print('  - Mopidy event broadcasting disabled')
            print('  - WebSocket events not working')
            print('  - No actions performed in Mopidy')
        else:
            print('✅ Event system is working!')
        
        mopidy.disconnect()
        print('👋 Disconnected.')

if __name__ == '__main__':
    main()
