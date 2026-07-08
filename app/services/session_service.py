import re
import time

import bds.bds_serial as bds_ser
import config_manager


def extract_and_convert_hex(string):
    pattern = r"(0x[0-9A-Fa-f]+)\s+(0x[0-9A-Fa-f]+)"
    match = re.search(pattern, string)
    if match:
        hex1, hex2 = match.groups()
        if int(hex1, 16) % 4 != 0:
            return None
        return hex1, hex2
    return None


def get_hw_mode(js_cfg):
    return 'jlink' if js_cfg.get('hw_sel', '1') == '1' else 'serial'


def get_target_display_name(js_cfg):
    if get_hw_mode(js_cfg) == 'jlink':
        return js_cfg['jk_chip'][0]
    return js_cfg.get('ser_des') or js_cfg.get('ser_com') or '未选择串口'


def get_endpoint_display(js_cfg):
    if get_hw_mode(js_cfg) == 'jlink':
        return '速度 {} kHz'.format(js_cfg['jk_speed'])
    return '波特率 {}'.format(js_cfg['ser_baud'][0])


def get_line_break_display(line_break):
    if line_break == '\r\n':
        return r'\r\n'
    if line_break == '\n':
        return r'\n'
    return 'none'


def get_line_break_value(display_value):
    if display_value == r'\r\n':
        return '\r\n'
    if display_value == r'\n':
        return '\n'
    return ''


def normalize_ui_layout(value):
    if value in ('terminal', 'session_terminal'):
        return 'terminal'
    return 'log'


def is_terminal_layout(js_cfg):
    return normalize_ui_layout(js_cfg.get('ui_layout', 'log')) == 'terminal'


def extract_outside_brackets_corrected(text):
    pattern = r'\([^)]*\)|（[^）]*）'
    return re.sub(pattern, '', text).strip()


def update_user_input_list(input_data, user_input_list):
    if not isinstance(input_data, str) or input_data.strip() == '':
        return user_input_list

    outside = extract_outside_brackets_corrected(input_data)
    if outside == '':
        return user_input_list

    user_input_list = [item for item in user_input_list if item.strip() != '']
    user_input_list = [
        item for item in user_input_list
        if extract_outside_brackets_corrected(item) != outside
    ]
    if len(user_input_list) >= 29:
        user_input_list.pop(-1)
    user_input_list.insert(0, input_data)
    return user_input_list


def get_next_history_item(lst, current_index, direction):
    if not lst:
        return None, None
    if current_index is None:
        current_index = 0
    if direction == 'up':
        new_index = (current_index - 1) % len(lst)
    elif direction == 'down':
        new_index = (current_index + 1) % len(lst)
    else:
        return None, None
    return lst[new_index], new_index


def jk_open_device(obj, jk_cfg):
    start_address = None
    range_size = 0
    if jk_cfg['rtt_block_address'][0] and jk_cfg['rtt_block_address'][1]:
        start_address = int(jk_cfg['rtt_block_address'][0], 16)
        range_size = int(jk_cfg['rtt_block_address'][1], 16)
    return obj.hw_open(
        speed=jk_cfg.get('jk_speed', 4000),
        chip=jk_cfg['jk_chip'][0],
        reset_flag=jk_cfg.get('jk_con_reset', True),
        start_address=start_address,
        range_size=range_size,
    )


def jk_connect_log_lines(jk_cfg):
    lines = [
        '[J_Link LOG]sn:%d\n' % jk_cfg.get('_jk_sn', 0),
        '[J_Link LOG]过滤配置:%s\n' % ','.join(jk_cfg['filter'].split('&&')),
        '[J_Link LOG]芯片型号:%s\n' % jk_cfg['jk_chip'][0],
    ]
    if jk_cfg.get('jk_con_reset', True):
        lines.append('[J_Link LOG]J_Link复位MCU.\n')
    else:
        lines.append('[J_Link LOG]J_Link没有复位MCU.\n')
    if 'H7' in jk_cfg['jk_chip'][0].upper():
        lines.append('[J_Link LOG]STM32H7调试时钟: 自动使能\n')
    return lines


def connect_jlink(hw_obj, js_cfg):
    connection_success = jk_open_device(hw_obj, js_cfg)
    if connection_success:
        js_cfg['_jk_sn'] = hw_obj.get_hw_serial_number()
        return True, jk_connect_log_lines(js_cfg)
    return False, ['[J_Link LOG]J_Link打开失败\n']


def connect_serial(hw_obj, js_cfg):
    if bds_ser.sync_serial_config(js_cfg):
        config_manager.save_config(js_cfg)
    cur_baud = int(js_cfg['ser_baud'][0])
    lines = [
        '[Serial LOG]com description: %s\n' % js_cfg['ser_des'],
        '[Serial LOG]baudrare: %d\n' % cur_baud,
    ]
    hw_obj.hw_open(port=js_cfg['ser_com'], baud=cur_baud, rx_buffer_size=10240)
    if hw_obj.hw_is_open():
        lines.append('[Serial LOG]串口已打开\n')
        return True, lines
    lines.append('[Serial LOG]串口打开失败\n')
    return False, lines


def disconnect_hw(hw_obj, mode):
    hw_obj.close_timestamp()
    hw_obj.hw_close()
    time.sleep(0.1)
    if mode == 'jlink':
        return ['[J_Link LOG]J_Link断开连接\n']
    return ['[Serial LOG]串口关闭！\n']


def send_payload(hw_obj, js_cfg, input_data, tx_data_type, save_history=True):
    if not hw_obj.hw_is_open():
        return 0, '请先连接硬件！', False

    if save_history:
        js_cfg['user_input_data'] = update_user_input_list(input_data, js_cfg['user_input_data'])
        config_manager.save_config(js_cfg)

    if tx_data_type == 'HEX':
        try:
            payload = [int(i, 16) for i in input_data.split()]
            hw_obj.hw_write(payload)
            return len(payload), '', True
        except Exception:
            return 0, '数据格式错误。数据类型请选择HEX，数据之间用空格隔开。', False

    try:
        payload_text = extract_outside_brackets_corrected(input_data) + js_cfg['line_break']
        hw_obj.hw_write([ord(i) for i in payload_text])
        return len(payload_text.encode('utf-8', errors='ignore')), '', True
    except Exception as exc:
        return 0, str(exc), False


def save_console_history(js_cfg, line):
    if not line:
        return
    js_cfg['user_input_data'] = update_user_input_list(line, js_cfg['user_input_data'])
    config_manager.save_config(js_cfg)


def send_terminal_char(hw_obj, char_code):
    if not hw_obj.hw_is_open():
        return 0, False
    hw_obj.hw_write([char_code])
    return 1, True
