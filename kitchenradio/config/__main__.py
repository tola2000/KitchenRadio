"""
Command-line interface for KitchenRadio configuration
"""

import sys
from . import print_config, print_pin_map

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--pins':
        print_pin_map()
    elif len(sys.argv) > 1 and sys.argv[1] == '--all':
        print_config()
        print()
        print_pin_map()
    else:
        print_config()
