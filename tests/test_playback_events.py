#!/usr/bin/python

import time
import argparse
import logging
from mopidy_json_client import MopidyClient

def print_track_info(tl_track):
    track = tl_track.get('track') if tl_track else None
    if not track:
        print('No Track')
        return

    trackinfo = {
        'name': track.get('name'),
        'artists': ', '.join([artist.get('name') for artist in track.get('artists')])
    }
    print('🎵 Now playing: {artists} - {name}'.format(**trackinfo))

def on_connection_change(is_connected):
    if is_connected:
        print('✓ Connected to Mopidy server')
    else:
        print('✗ Disconnected from Mopidy server')

def on_error(error):
    print(f'❌ Error: {error}')

def main():
    parser = argparse.ArgumentParser(description='Start playing and monitor events from Mopidy')
    parser.add_argument('--host', '-H', 
                        default='localhost', 
                        help='Mopidy server host (default: localhost)')
    parser.add_argument('--port', '-p', 
                        type=int, 
                        default=6680, 
                        help='Mopidy server port (default: 6680)')
    parser.add_argument('--debug', '-d',
                        action='store_true',
                        help='Enable debug logging')
    parser.add_argument('--uri', '-u',
                        default='spotify:playlist:37i9dQZF1DXcBWIGoYBM5M',
                        help='URI to play (default: Spotify Today\'s Top Hits)')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    # Construct WebSocket URL
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'Connecting to Mopidy server at {ws_url}')
    
    # Create client
    mopidy = MopidyClient(
        ws_url=ws_url, 
        debug=args.debug,
        connection_handler=on_connection_change,
        error_handler=on_error,
        autoconnect=True,
        retry_max=3,
        retry_secs=5
    )
    
    # Wait for connection
    print('Waiting for connection...')
    if not mopidy.connect(wait_secs=10):
        print('❌ Failed to connect to Mopidy server!')
        return
    
    print('✅ Connected successfully!')
    
    # Set up event listeners
    print('Setting up event listeners...')
    mopidy.bind_event('track_playback_started', print_track_info)
    mopidy.bind_event('track_playback_resumed', print_track_info)
    mopidy.bind_event('track_playback_paused', lambda tl_track: print('⏸️ Track paused'))
    mopidy.bind_event('track_playback_ended', lambda tl_track: print('⏹️ Track ended'))
    mopidy.bind_event('playback_state_changed', 
                     lambda old_state, new_state: print(f'🔄 State: {old_state} → {new_state}'))
    mopidy.bind_event('volume_changed', 
                     lambda volume: print(f'🔊 Volume: {volume}%'))
    
    try:
        # Clear current tracklist
        print('🧹 Clearing tracklist...')
        mopidy.tracklist.clear()
        
        # Add track to tracklist
        print(f'➕ Adding URI: {args.uri}')
        tracks = mopidy.tracklist.add(uris=[args.uri])
        
        if tracks:
            print(f'✅ Added {len(tracks)} track(s) to tracklist')
            
            # Start playback
            print('▶️ Starting playback...')
            mopidy.playback.play()
            
            print('\n' + '='*60)
            print('🎵 Music should be playing! Monitoring events...')
            print('Commands you can try:')
            print('  - Music should start automatically')
            print('  - Try changing volume on your Mopidy interface')
            print('  - Try pause/resume')
            print('Press Ctrl+C to stop.')
            print('='*60)
            
            # Wait a bit for playback to start
            time.sleep(2)
            
            # Try to get current state
            try:
                state = mopidy.playback.get_state(timeout=3)
                print(f'📊 Current state: {state}')
            except:
                pass
            
            # Main monitoring loop
            while True:
                time.sleep(1.0)
                
        else:
            print('❌ Could not add tracks. Check if the URI is valid and accessible.')
            print('Available URI schemes:')
            try:
                schemes = mopidy.core.get_uri_schemes(timeout=3)
                print(f'📋 Supported schemes: {", ".join(schemes)}')
            except:
                print('Could not get URI schemes')
                
    except Exception as e:
        print(f'❌ Error during playback setup: {e}')
        print('💡 Try these URIs instead:')
        print('  - file:///path/to/music.mp3 (local file)')
        print('  - http://stream-url (radio stream)')
        print('  - spotify:track:4iV5W9uYEdYUVa79Axb7Rh (Spotify track)')
        
    except KeyboardInterrupt:
        print('\n🛑 Stopping...')
        try:
            mopidy.playback.stop()
            mopidy.tracklist.clear()
        except:
            pass
        mopidy.disconnect()
        print('👋 Disconnected.')

if __name__ == '__main__':
    main()
