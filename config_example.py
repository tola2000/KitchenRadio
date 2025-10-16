# MoOde Audio Controller Configuration
# Copy this file to config.py and modify as needed

# Default MoOde server settings
MOODE_HOST = "localhost"
MOODE_PORT = 80

# Connection settings
TIMEOUT = 10  # seconds
MAX_RETRIES = 3

# CLI settings
DEFAULT_JSON_OUTPUT = False

# Volume settings
DEFAULT_VOLUME_STEP = 5  # Volume change step for up/down commands

# Example configurations for different setups:

# Local MoOde installation
# MOODE_HOST = "localhost"
# MOODE_PORT = 80

# Remote MoOde server
# MOODE_HOST = "192.168.1.100"
# MOODE_PORT = 80

# MoOde with custom port
# MOODE_HOST = "moode.local"
# MOODE_PORT = 8080
