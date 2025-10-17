#!/usr/bin/python

import time
import argparse
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
    print('Now playing: {artists} - {name}'.format(**trackinfo))

def main():
    parser = argparse.ArgumentParser(description='Monitor now playing track from Mopidy')
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
    
    # Construct WebSocket URL
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'Connecting to Mopidy server at {ws_url}')
    
    # Create client with custom host and wait for connection
    mopidy = MopidyClient(ws_url=ws_url, debug=args.debug, autoconnect=True)
    
    # Wait for connection to be established
    print('Waiting for connection...')
    if not mopidy.connect(wait_secs=10):
        print('Failed to connect to Mopidy server!')
        return
    
    print('Connected successfully!')
    
    # Bind event after connection is established
    mopidy.bind_event('track_playback_started', print_track_info)
    
    # Also bind to track_playback_resumed and track_playback_paused for more coverage
    mopidy.bind_event('track_playback_resumed', print_track_info)
    mopidy.bind_event('track_playback_paused', lambda tl_track: print('Track paused'))
    
    # Get current track if already playing
    try:
        current_track = mopidy.playback.get_current_tl_track()
        if current_track:
            print('Currently playing:')
            print_track_info(current_track)
        else:
            print('No track currently playing')
    except Exception as e:
        print(f'Error getting current track: {e}')
    
    # Main loop
    try:
        print('Monitoring now playing... Press Ctrl+C to stop.')
        while True:
            time.sleep(1.0)  # Increased sleep time
    except KeyboardInterrupt:
        print('\nStopping...')
        mopidy.disconnect()

if __name__ == '__main__':
    main()
