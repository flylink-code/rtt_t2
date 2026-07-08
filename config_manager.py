import os
import json
import sys

from app.chip_catalog import DEFAULT_CHIP_CATALOG, normalize_chip_config
from app.release_info import LOG_DIR_NAME

DEPRECATED_CONFIG_KEYS = (
    "jk_debug_run",
    "jk_run_after_rtt",
    "jk_h7_dbg_enable",
)

DEFAULT_RTT_SEARCH_START = '0x20000000'
DEFAULT_RTT_SEARCH_SIZE = '0x20000'
DEFAULT_RTT_BLOCK_ADDRESS = [DEFAULT_RTT_SEARCH_START, DEFAULT_RTT_SEARCH_SIZE]

DEFAULT_CONFIG = {
    "jk_chip": [
        "STM32H743II",
    ],
    "jk_chip_catalog": DEFAULT_CHIP_CATALOG,
    "jk_interface": [
        "SWD"
    ],
    "jk_con_reset": False,
    "jk_speed": 4000,
    "hw_sel": "1",
    "filter": "",
    "filter_en": False,
    "font": [
        "Cascadia Mono",
        "Microsoft YaHei UI"
    ],
    "font_size": "13",
    "tx_line": "\n",
    "user_input_data": [
        "123"
    ],
    "curves_name": "X&&Y&&Z",
    "y_range": [
        -100,
        100
    ],
    "y_label_text": "m/s^2",
    "ser_baud": [
        2000000,
        115200,
        941176,
        1152000,
        9600,
        19200
    ],
    "ser_com": "COM1",
    "ser_des": "通信端口 (COM1)",
    "char_format": "asc",
    "update_flag": True,
    "line_break": "\n",
    "ui_theme": "dark",
    "ui_layout": "log",
    "terminal_autoscroll": True,
    "terminal_paused": False,
    "send_panel_mode": "expanded",
    "custom_commands": [
        {"name": "示例-帮助", "content": "help", "tx_type": "ASC"},
        {"name": "示例-回车", "content": "", "tx_type": "ASC"}
    ],
    "rtt_block_address": list(DEFAULT_RTT_BLOCK_ADDRESS),
    "log_save_dir": "",
}

def get_app_dir():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def get_config_path():
    return os.path.join(get_app_dir(), 'config.json')

def get_log_dir():
    return os.path.join(get_app_dir(), LOG_DIR_NAME)

def normalize_rtt_block_address(addresses):
    if not isinstance(addresses, list) or len(addresses) < 2:
        return list(DEFAULT_RTT_BLOCK_ADDRESS)
    start = str(addresses[0] or '').strip()
    size = str(addresses[1] or '').strip()
    if start and size:
        return [start, size]
    return list(DEFAULT_RTT_BLOCK_ADDRESS)

def format_rtt_search_text(addresses):
    start, size = normalize_rtt_block_address(addresses)
    return '%s %s' % (start, size)

def parse_rtt_search_values(addresses):
    start_hex, size_hex = normalize_rtt_block_address(addresses)
    return int(start_hex, 16), int(size_hex, 16)

def ensure_log_dir():
    log_dir = get_log_dir()
    legacy_dir = os.path.join(get_app_dir(), 'aaa_log')
    if os.path.isdir(legacy_dir) and not os.path.exists(log_dir):
        os.rename(legacy_dir, log_dir)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

def load_config():
    config_path = get_config_path()
    if not os.path.exists(config_path):
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    for key, value in DEFAULT_CONFIG.items():
        if key not in config:
            config[key] = value
    for key in DEPRECATED_CONFIG_KEYS:
        config.pop(key, None)
    migrated = 'jk_chip_catalog' not in config
    config = normalize_chip_config(config)
    old_rtt = config.get('rtt_block_address')
    config['rtt_block_address'] = normalize_rtt_block_address(old_rtt)
    if migrated or old_rtt != config['rtt_block_address']:
        save_config(config)
    return config

def save_config(config):
    with open(get_config_path(), 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def initialize_app_environment():
    load_config()
    return ensure_log_dir()
