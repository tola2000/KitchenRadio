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
    print('Now playing: {artists} - {name}'.format(**trackinfo))

def on_connection_change(is_connected):
    if is_connected:
        print('✓ Connected to Mopidy server')
    else:
        print('✗ Disconnected from Mopidy server')

def on_error(error):
    print(f'Error: {error}')

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
    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Construct WebSocket URL
    ws_url = f'ws://{args.host}:{args.port}/mopidy/ws'
    print(f'Connecting to Mopidy server at {ws_url}')
    
    # Create client with connection and error handlers
    mopidy = MopidyClient(
        ws_url=ws_url, 
        debug=args.debug,
        connection_handler=on_connection_change,
        error_handler=on_error,
        autoconnect=True,
        retry_max=3,
        retry_secs=5
    )
    
    # Wait for connection to be established
    print('Waiting for connection...')
    if not mopidy.connect(wait_secs=15):
        print('Failed to connect to Mopidy server!')
        print('Make sure Mopidy is running and the HTTP extension is enabled.')
        return
    
    print('Connected successfully!')
    
    # Bind multiple events for better coverage
    mopidy.bind_event('track_playback_started', print_track_info)
    mopidy.bind_event('track_playback_resumed', print_track_info)
    mopidy.bind_event('track_playback_paused', lambda tl_track: print('⏸ Track paused'))
    mopidy.bind_event('track_playback_ended', lambda tl_track: print('⏹ Track ended'))
    
    if args.verbose:
        # Bind additional events for verbose mode
        mopidy.bind_event('playback_state_changed', 
                         lambda old_state, new_state: print(f'State: {old_state} → {new_state}'))
        mopidy.bind_event('volume_changed', 
                         lambda volume: print(f'Volume: {volume}%'))
    
    # Get current track if already playing
    try:
        current_track = mopidy.playback.get_current_tl_track()
        if current_track:
            print('\nCurrently playing:')
            print_track_info(current_track)
            
            # Get playback state
            state = mopidy.playback.get_state()
            print(f'State: {state}')
        else:
            print('No track currently playing')
    except Exception as e:
        print(f'Error getting current track: {e}')
    
    print('\n' + '='*50)
    print('Monitoring events... Press Ctrl+C to stop.')
    print('='*50)
    
    # Main loop
    try:
        while True:
            # Check connection status periodically
            if not mopidy.is_connected():
                print('Warning: Connection lost, attempting to reconnect...')
            time.sleep(1.0)
    except KeyboardInterrupt:
        print('\nStopping...')
        mopidy.disconnect()
        print('Disconnected.')

if __name__ == '__main__':
    main()
