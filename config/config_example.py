"""
Configuration settings for KitchenRadio
"""

# MPD server settings
MPD_HOST = "192.168.1.4"
MPD_PORT = 6600
MPD_PASSWORD = None  # Set if MPD requires authentication

# Default settings
DEFAULT_VOLUME = 50
DEFAULT_TIMEOUT = 5

# Radio stations
RADIO_STATIONS = {
    "groove_salad": "http://ice1.somafm.com/groovesalad-256-mp3",
    "def_con": "http://ice1.somafm.com/defcon-256-mp3", 
    "bbc_radio1": "http://stream.live.vc.bbcmedia.co.uk/bbc_radio_one",
    "jazz24": "http://jazz24-ice.streamguys1.com/jazz24-7"
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
