import os
import json

CONFIG_DIR = "data"
CONFIG_FILE = "config.json"
DEFAULT_OPACITY = 50
CONFIG_PATH = os.path.join(CONFIG_DIR, CONFIG_FILE)

def load_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
            opacity = int(config.get('opacity_percent', DEFAULT_OPACITY))
            opacity = max(0, min(50, opacity))
            return opacity
    except:
        return DEFAULT_OPACITY

def save_config(_current_opacity):
    config = {'opacity_percent': _current_opacity}

    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
    except:
        return
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=4)
    except:
        pass