#!/usr/bin/python

import time
import argparse
from mopidy_json_client import MopidyClient

def main():
    parser = argparse.ArgumentParser(description='Force trigger Mopidy events')
    parser.add_argument('--host', '-H', default='localhost', help='Mopidy host')
    parser.add_argument('--port', '-p', type=int, default=6680, help='Mopidy port')
    
    args = parser.parse_args()
    
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'🔌 Connecting to {ws_url}')
    
    events_received = []
    
    def event_logger(event, **data):
        events_received.append((event, data))
        print(f'📡 EVENT: {event} -> {data}')
    
    # Create client
    mopidy = MopidyClient(ws_url=ws_url, autoconnect=True)
    
    if not mopidy.connect(wait_secs=5):
        print('❌ Connection failed!')
        return
    
    print('✅ Connected!')
    
    # Set up a general event handler
    mopidy.listener.on_event = event_logger
    
    print('\n🔧 ATTEMPTING TO TRIGGER EVENTS...')
    print('=' * 45)
    
    # Method 1: Try to clear tracklist (should trigger tracklist_changed)
    print('1️⃣ Clearing tracklist...')
    try:
        result = mopidy.tracklist.clear(timeout=3)
        print(f'   Result: {result}')
        time.sleep(1)
    except Exception as e:
        print(f'   ❌ Failed: {e}')
    
    # Method 2: Try to add a dummy URI (might fail but could trigger events)
    print('2️⃣ Adding test URI...')
    try:
        result = mopidy.tracklist.add(uris=['dummy:test'], timeout=3)
        print(f'   Result: {result}')
        time.sleep(1)
    except Exception as e:
        print(f'   ❌ Failed: {e}')
    
    # Method 3: Try playback commands
    print('3️⃣ Testing playback commands...')
    try:
        state = mopidy.playback.get_state(timeout=3)
        print(f'   Current state: {state}')
        
        # Try to start playback (might fail but could trigger state change)
        mopidy.playback.play(timeout=3)
        time.sleep(1)
        
        # Try to stop
        mopidy.playback.stop(timeout=3)
        time.sleep(1)
        
    except Exception as e:
        print(f'   ❌ Failed: {e}')
    
    # Method 4: Test with a working stream
    print('4️⃣ Testing with radio stream...')
    try:
        # Add a known working stream
        stream_uri = 'http://ice1.somafm.com/groovesalad-256-mp3'
        print(f'   Adding: {stream_uri}')
        
        mopidy.tracklist.clear(timeout=3)
        result = mopidy.tracklist.add(uris=[stream_uri], timeout=5)
        
        if result:
            print(f'   ✅ Added stream, starting playback...')
            mopidy.playback.play(timeout=3)
            
            # Let it play for a few seconds
            print('   🎵 Playing for 5 seconds...')
            time.sleep(5)
            
            print('   ⏹️ Stopping...')
            mopidy.playback.stop(timeout=3)
        else:
            print('   ❌ Could not add stream')
            
    except Exception as e:
        print(f'   ❌ Stream test failed: {e}')
    
    print('\n' + '=' * 45)
    print(f'📊 RESULTS: {len(events_received)} events received')
    
    if events_received:
        print('✅ Events are working! Received:')
        for i, (event, data) in enumerate(events_received, 1):
            print(f'  {i}. {event}: {data}')
    else:
        print('❌ No events received. Possible issues:')
        print('  - Mopidy events not enabled')
        print('  - WebSocket event broadcasting disabled') 
        print('  - Client event binding not working')
        print('\n💡 Check your Mopidy configuration:')
        print('  [http]')
        print('  enabled = true')
        print('  hostname = 0.0.0.0')
        print('  port = 6680')
    
    mopidy.disconnect()
    print('👋 Done!')

if __name__ == '__main__':
    main()
