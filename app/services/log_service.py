import logging as log
import re

COLOR_PATTERN = re.compile(r'BDSCOL\((\d{1,8})\)', re.I)
BDSCOL_STRIP = re.compile(r'BDSCOL\([0-9]{1,8}\)')

DEFAULT_LOG_COLOR = 0xE5E7EB
LEGACY_DEFAULT_LOG_COLOR = DEFAULT_LOG_COLOR


def delete_str(pat, s, reverse=False, s_sub=''):
    matches = re.findall(pat, s)
    if reverse:
        matches = [match for match in matches if s_sub in match]
    for match in matches:
        s = s.replace(match, '')
    return s


def remove_line(patterns, line, only_exclude):
    if not patterns:
        return line
    if any(pattern in line for pattern in patterns) != only_exclude:
        return line
    return ''


def filter_log_text(log_data, filter_pat, remain_str='', only_exclude=True):
    raw_s = remain_str + ''.join(log_data)
    log_lines = raw_s.split('\n')
    filtered_lines = []
    updated_remain_str = ''

    last_index = len(log_lines) - 1
    for idx, line in enumerate(log_lines):
        if idx < last_index:
            filtered_lines.append(remove_line(filter_pat, line + '\n', only_exclude))
        elif line.endswith('\n'):
            filtered_lines.append(remove_line(filter_pat, line + '\n', only_exclude))
        else:
            updated_remain_str = line

    return ''.join(filtered_lines), updated_remain_str


def db_data_check_error(s):
    err_cnt = 0
    err_chr = chr(0)
    for char in s:
        if char > '~' or char == err_chr:
            err_cnt += 1
            if err_cnt > 100:
                return True
    return False


def parse_colored_segments(text):
    """Parse log text into (text, color_int) segments for terminal rendering."""
    segments = []
    sv = ''
    color = 0
    pre_color = -1
    line_parts = re.findall('.+\n', text)
    if not line_parts and text:
        line_parts = [text]

    for part in line_parts:
        match = COLOR_PATTERN.search(part)
        if match is None:
            if pre_color >= 0 and sv:
                segments.append((sv, pre_color))
                sv = ''
                pre_color = -1
            sv += part
            color = -1
        else:
            if sv and color == -1:
                segments.append((sv, 0))
                sv = ''
            try:
                color = int(match.group(1))
            except Exception as exc:
                log.info('color parse error: %s in %s', exc, part)
                color = 0
            if pre_color < 0:
                pre_color = color
            if color == pre_color:
                temp_s = BDSCOL_STRIP.sub('', part)
                sv += temp_s
            else:
                if sv:
                    segments.append((sv, pre_color))
                sv = BDSCOL_STRIP.sub('', part)
                pre_color = color

    if color < 0:
        color = DEFAULT_LOG_COLOR
    if sv:
        segments.append((sv, color))
    return segments


class LogProcessor:
    def __init__(self):
        self.remain_str = ''

    def process_queue(self, hw_obj, js_cfg, filter_enabled, filter_text, filter_inverse):
        raw_log = []
        hw_obj.read_data_queue(raw_log)
        if not raw_log:
            return None

        if js_cfg['char_format'] == 'hex':
            text = ''.join(raw_log)
            return {'kind': 'plain', 'text': text, 'save_text': text, 'size': len(text)}

        filter_pat = []
        only_exclude = True
        if filter_enabled and filter_text:
            filter_pat = filter_text.split('&&')
            if filter_inverse:
                only_exclude = False

        new_log, self.remain_str = filter_log_text(
            raw_log, filter_pat, self.remain_str, only_exclude
        )

        if js_cfg['char_format'] == 'asc' and db_data_check_error(new_log):
            return {
                'kind': 'error',
                'text': "RTT数据出错，可能需要重启设备！ + error data:[" + new_log[0:20] + "]\n",
                'save_text': '',
                'size': 0,
            }

        segments = parse_colored_segments(new_log)
        save_text = ''.join(part for part, _ in segments)
        return {
            'kind': 'colored',
            'segments': segments,
            'save_text': save_text,
            'size': len(save_text),
        }
