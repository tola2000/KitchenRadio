#!/usr/bin/python

import time
import argparse
from mopidy_json_client import MopidyClient

def main():
    parser = argparse.ArgumentParser(description='Simple playback test and event monitor')
    parser.add_argument('--host', '-H', default='localhost', help='Mopidy host')
    parser.add_argument('--port', '-p', type=int, default=6680, help='Mopidy port')
    
    args = parser.parse_args()
    
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'Connecting to {ws_url}')
    
    mopidy = MopidyClient(ws_url=ws_url, autoconnect=True)
    
    if not mopidy.connect(wait_secs=5):
        print('❌ Connection failed!')
        return
    
    print('✅ Connected!')
    
    # Simple event handlers
    def on_any_event(**kwargs):
        print(f'📡 Event received: {kwargs}')
    
    # Bind to ALL events to see what we get
    mopidy.bind_event('track_playback_started', on_any_event)
    mopidy.bind_event('track_playback_paused', on_any_event)
    mopidy.bind_event('track_playback_resumed', on_any_event)
    mopidy.bind_event('track_playback_ended', on_any_event)
    mopidy.bind_event('playback_state_changed', on_any_event)
    mopidy.bind_event('volume_changed', on_any_event)
    
    print('🎧 Event listeners ready!')
    
    try:
        # Get available backends
        print('📋 Checking available URI schemes...')
        schemes = mopidy.core.get_uri_schemes(timeout=3)
        print(f'Available: {", ".join(schemes)}')
        
        # Try to get current volume to test basic API
        volume = mopidy.mixer.get_volume(timeout=3)
        print(f'🔊 Current volume: {volume}%')
        
        # Test volume change to trigger an event
        print('🔧 Testing volume change to trigger event...')
        if volume is not None:
            # Change volume slightly to trigger event
            new_volume = min(100, volume + 5)
            mopidy.mixer.set_volume(new_volume)
            print(f'🔊 Set volume to {new_volume}%')
            time.sleep(1)
            
            # Change it back
            mopidy.mixer.set_volume(volume)
            print(f'🔊 Restored volume to {volume}%')
        
        print('\n' + '='*40)
        print('🎵 Monitoring for events...')
        print('Try these actions in your Mopidy interface:')
        print('  - Change volume')
        print('  - Start playing music')
        print('  - Pause/resume')
        print('Press Ctrl+C to stop.')
        print('='*40)
        
        while True:
            time.sleep(1.0)
            
    except Exception as e:
        print(f'❌ Error: {e}')
    except KeyboardInterrupt:
        print('\n🛑 Stopping...')
        mopidy.disconnect()
        print('👋 Done!')

if __name__ == '__main__':
    main()
