#!/usr/bin/python

import time
import argparse
import logging
from mopidy_json_client import MopidyClient

def print_track_info(tl_track):
    track = tl_track.get('track') if tl_track else None
    if not track:
        print('🎵 Track info not available')
        return

    trackinfo = {
        'name': track.get('name', 'Unknown'),
        'artists': ', '.join([artist.get('name', 'Unknown') for artist in track.get('artists', [])])
    }
    print('🎵 Now playing: {artists} - {name}'.format(**trackinfo))

def main():
    parser = argparse.ArgumentParser(description='Test playback and events with radio stream')
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
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'Connecting to Mopidy server at {ws_url}')
    
    mopidy = MopidyClient(ws_url=ws_url, debug=args.debug, autoconnect=True)
    
    if not mopidy.connect(wait_secs=10):
        print('❌ Failed to connect!')
        return
    
    print('✅ Connected!')
    
    # Event listeners
    mopidy.bind_event('track_playback_started', print_track_info)
    mopidy.bind_event('track_playback_resumed', print_track_info)
    mopidy.bind_event('track_playback_paused', lambda **kwargs: print('⏸️ Paused'))
    mopidy.bind_event('track_playback_ended', lambda **kwargs: print('⏹️ Ended'))
    mopidy.bind_event('playback_state_changed', 
                     lambda old_state, new_state: print(f'🔄 {old_state} → {new_state}'))
    mopidy.bind_event('volume_changed', 
                     lambda volume: print(f'🔊 Volume: {volume}%'))
    
    # Test with a radio stream (should work on most Mopidy setups)
    radio_streams = [
        'http://ice1.somafm.com/groovesalad-256-mp3',  # SomaFM Groove Salad
        'http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one',  # BBC Radio 1
        'http://ice1.somafm.com/defcon-256-mp3',  # SomaFM DEF CON Radio
    ]
    
    try:
        print('🧹 Clearing tracklist...')
        mopidy.tracklist.clear()
        
        # Try each radio stream
        for i, stream_url in enumerate(radio_streams, 1):
            print(f'🔗 Trying stream {i}: {stream_url}')
            try:
                tracks = mopidy.tracklist.add(uris=[stream_url], timeout=5)
                if tracks:
                    print(f'✅ Added stream to tracklist')
                    break
            except Exception as e:
                print(f'❌ Failed to add stream {i}: {e}')
                continue
        else:
            print('❌ Could not add any streams. Let\'s check what backends are available:')
            try:
                schemes = mopidy.core.get_uri_schemes(timeout=5)
                print(f'📋 Available schemes: {", ".join(schemes)}')
            except:
                print('Could not get schemes')
            return
        
        print('▶️ Starting playback...')
        mopidy.playback.play()
        
        print('\n' + '='*50)
        print('🎵 Stream should be playing!')
        print('You should see events when:')
        print('  - Playback starts')
        print('  - You change volume')
        print('  - Stream changes tracks')
        print('Press Ctrl+C to stop.')
        print('='*50)
        
        # Monitor for events
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print('\n🛑 Stopping playback...')
        try:
            mopidy.playback.stop()
        except:
            pass
        mopidy.disconnect()
        print('👋 Done!')

if __name__ == '__main__':
    main()
