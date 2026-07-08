import os
import sys
import time

import pylink
from pylink import library as pylink_library

from bds.hw_base import HardWareBase

JLINK_DOWNLOAD_URL = 'https://www.segger.com/downloads/jlink/'
JLINK_DLL_ENV = 'JLINK_SDK'
STM32H7_DBGMCU_CR = 0x58000404
STM32H7_DBGMCU_ENABLE_MASK = (
    0x00000001 |  # DBG_SLEEPD1
    0x00000002 |  # DBG_STOPD1
    0x00000004 |  # DBG_STANDBYD1
    0x00200000 |  # DBG_CKD1EN
    0x00400000    # DBG_CKD3EN
)
RTT_MAGIC = 'SEGGER RTT'
RTT_READY_TIMEOUT_S = 5.0
RTT_CB_SIZE = 0xC0
RTT_CB_AUP0_PBUFFER_OFF = 0x1C
RTT_CB_AUP0_SIZE_OFF = 0x20
RTT_CB_AUP0_WROFF_OFF = 0x24
DTCM_RTT_UP_BUF = 0x200000C0
DTCM_RTT_UP_SIZE = 1024

if sys.platform.startswith('win'):
    import winreg

    JLINK_REGISTRY_KEYS = (
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\SEGGER\J-Link'),
        (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\SEGGER\J-Link'),
        (winreg.HKEY_CURRENT_USER, r'SOFTWARE\SEGGER\J-Link'),
    )
else:
    JLINK_REGISTRY_KEYS = ()


def jlink_dll_name():
    if sys.platform.startswith('win'):
        return pylink_library.Library.get_appropriate_windows_sdk_name() + '.dll'
    return pylink_library.Library.JLINK_SDK_NAME + '.so'


def resolve_jlink_dll(install_dir):
    dll_path = os.path.join(install_dir, jlink_dll_name())
    if os.path.isfile(dll_path):
        return dll_path
    return None


def read_registry_install_paths():
    install_paths = []
    seen = set()
    for hive, subkey in JLINK_REGISTRY_KEYS:
        try:
            with winreg.OpenKey(hive, subkey) as key:
                install_path, _ = winreg.QueryValueEx(key, 'InstallPath')
        except OSError:
            continue
        if install_path and install_path not in seen and os.path.isdir(install_path):
            seen.add(install_path)
            install_paths.append(install_path)
    return install_paths


def find_jlink_dll():
    env_path = os.environ.get(JLINK_DLL_ENV)
    if env_path:
        if os.path.isfile(env_path):
            return env_path
        resolved = resolve_jlink_dll(env_path)
        if resolved:
            return resolved

    for install_dir in read_registry_install_paths():
        resolved = resolve_jlink_dll(install_dir)
        if resolved:
            return resolved

    if sys.platform.startswith('win'):
        dll_paths = list(pylink_library.Library.find_library_windows())
        if dll_paths:
            return dll_paths[0]

    return None


def jlink_missing_message():
    return (
        '未找到 J-Link SDK (JLink_x64.dll / JLinkARM.dll)。'
        f'请先安装 SEGGER J-Link 软件: {JLINK_DOWNLOAD_URL} '
        f'或设置环境变量 {JLINK_DLL_ENV} 指向 DLL 文件。'
    )


def is_stm32h7_chip(chip):
    return 'H7' in chip.upper()


def convert_numbers_to_string(numbers, byte_size=4):
    byte_seq = (number.to_bytes(byte_size, 'little', signed=False) for number in numbers)
    return ''.join(map(lambda b: ''.join(chr(x) for x in b), byte_seq))


class BDS_Jlink(HardWareBase):
    def __init__(self, err_cb, warn_cb, chip='nRF52840_xxAA', speed=4000,
                 read_size=8192, tag_detect_timeout_s=6.0, read_rtt_data_interval_s=0.002, char_format='asc', **kwargs):
        super().__init__(err_cb, warn_cb, tag_detect_timeout_s, read_rtt_data_interval_s, char_format, **kwargs)
        self.jlink = None
        self._jlink_error = None
        self.speed = speed
        self.chip = chip
        self.rx_timeout = read_rtt_data_interval_s
        self.terminal = 0
        self.buffer_idx = 0
        self.read_size = read_size
        self.rtt_is_start = False
        self.clk = 0
        self.bytes_data = b''
        self.last_successful_sn = None

    def _ensure_jlink(self):
        if self.jlink is not None:
            return True
        if self._jlink_error is not None:
            return False

        dll_path = find_jlink_dll()
        try:
            lib = pylink_library.Library(dllpath=dll_path) if dll_path else pylink_library.Library()
            if lib.dll() is None:
                self._jlink_error = jlink_missing_message()
                return False
            self.jlink = pylink.JLink(lib=lib)
            return True
        except TypeError:
            self._jlink_error = jlink_missing_message()
            return False

    def _ensure_cpu_running(self):
        if self.jlink.halted():
            self.jlink.restart(skip_breakpoints=True)
        else:
            self.jlink._dll.JLINKARM_Go()

    def _enable_stm32h7_debug(self):
        current = self.jlink.memory_read32(STM32H7_DBGMCU_CR, 1)[0]
        enabled = current | STM32H7_DBGMCU_ENABLE_MASK
        if enabled != current:
            self.jlink.memory_write32(STM32H7_DBGMCU_CR, [enabled])
            print('STM32H7 DBGMCU enabled: 0x%08X -> 0x%08X' % (current, enabled))

    def _memory_contains_rtt_magic(self, address):
        try:
            num_bytes = self.jlink.memory_read32(address, 4)
            mem_data = convert_numbers_to_string(num_bytes)
            return RTT_MAGIC in mem_data
        except pylink.errors.JLinkException:
            return False

    def find_rtt_address(self, start_address, range_size):
        if not self._ensure_jlink():
            return -1
        if start_address is None:
            return -1
        num_bytes = self.jlink.memory_read32(start_address, (range_size // 4))
        mem_data = convert_numbers_to_string(num_bytes)
        return mem_data.find(RTT_MAGIC)

    def _is_rtt_cb_valid(self, block_address):
        if block_address is None:
            return False
        if not self._memory_contains_rtt_magic(block_address):
            return False
        try:
            words = self.jlink.memory_read32(block_address + RTT_CB_AUP0_PBUFFER_OFF, 2)
            p_buffer = words[0]
            size_of_buffer = words[1]
            return p_buffer == DTCM_RTT_UP_BUF and size_of_buffer == DTCM_RTT_UP_SIZE
        except pylink.errors.JLinkException:
            return False

    def _wait_for_rtt_ready(self, start_address, timeout_s=RTT_READY_TIMEOUT_S):
        if start_address is None:
            return False

        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self._is_rtt_cb_valid(start_address):
                return True
            time.sleep(0.02)
        return self._is_rtt_cb_valid(start_address)

    def _clear_rtt_control_block(self, block_address):
        try:
            self.jlink.memory_write32(block_address, [0] * (RTT_CB_SIZE // 4))
            print('已清除DTCM残留RTT控制块: 0x%x' % block_address)
        except pylink.errors.JLinkException as e:
            print('清除RTT控制块失败: %s' % e)

    def _log_rtt_cb_status(self, block_address):
        if block_address is None:
            return
        try:
            words = self.jlink.memory_read32(block_address + RTT_CB_AUP0_PBUFFER_OFF, 3)
            wr_off = self.jlink.memory_read32(block_address + RTT_CB_AUP0_WROFF_OFF, 1)[0]
            print('RTT CB: pBuffer=0x%08X size=%u WrOff=%u' % (words[0], words[1], wr_off))
        except pylink.errors.JLinkException:
            pass

    def _resolve_rtt_block_address(self, start_address, range_size, allow_search=True):
        if start_address is None:
            return None

        if not allow_search:
            print('使用固定RTT地址:0x%x (复位后跳过搜索, 避免残留控制块)' % start_address)
            return start_address

        if range_size > 0:
            offset = self.find_rtt_address(start_address, range_size)
            if offset >= 0:
                resolved = start_address + offset
                print('找到_SEGGER_RTT. 起始地址:0x%x, 地址偏移量:%d' % (resolved, offset))
                return resolved

        print('未在搜索范围内找到_SEGGER_RTT, 使用固定地址:0x%x' % start_address)
        return start_address

    def _start_rtt(self, block_address):
        self.jlink.swo_flush()
        self.jlink.rtt_stop()
        if block_address is not None and is_stm32h7_chip(self.chip):
            try:
                self.jlink.exec_command('SetRTTSearchRanges 0x20000000 0x20000')
            except Exception:
                pass
        self.jlink.rtt_start(block_address)
        self.rtt_is_start = True

    def hw_open(self, speed=4000, chip='nRF52840_xxAA', reset_flag=True, start_address=None, range_size=0,
                sn_no=None):
        if not self._ensure_jlink():
            self.err_cb(self._jlink_error + '\n')
            return False
        try:
            self.hw_para_init()
            self.speed = speed
            self.chip = chip

            if sn_no is None and self.last_successful_sn is not None:
                try:
                    self.jlink.open(serial_no=self.last_successful_sn)
                except pylink.errors.JLinkException:
                    self.jlink.open()
            else:
                self.jlink.open(serial_no=sn_no)

            self.jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
            self.jlink.set_speed(self.speed)
            self.jlink.connect(self.chip)

            if is_stm32h7_chip(chip):
                self._enable_stm32h7_debug()

            did_reset = reset_flag
            if did_reset:
                self.jlink.reset(ms=10, halt=True)
                if is_stm32h7_chip(chip):
                    self._enable_stm32h7_debug()
            # else: attach to already-running target without reset

            block_address = self._resolve_rtt_block_address(
                start_address, range_size, allow_search=not did_reset)

            if self.jlink.connected():
                if did_reset and block_address is not None:
                    self._clear_rtt_control_block(block_address)

                if did_reset or self.jlink.halted():
                    self._ensure_cpu_running()

                if block_address is not None:
                    if did_reset or not self._is_rtt_cb_valid(block_address):
                        if not self._wait_for_rtt_ready(block_address):
                            print('等待RTT控制块超时, 地址:0x%x (请确认固件已烧录且RTT已初始化)' % block_address)

                # Start host RTT reader only after target firmware has initialized CB.
                self._start_rtt(block_address)
                self._log_rtt_cb_status(block_address)

                print('jlink connect success...')
                self.last_successful_sn = self.jlink.serial_number
                return True
        except pylink.errors.JLinkException as e:
            self.err_cb('J_Link:%s\n' % e)
            print(e)
        return False

    def hw_close(self):
        if self.jlink is None:
            return
        if self.jlink.opened():
            try:
                self.rtt_is_start = False
                self.jlink.rtt_stop()
            except Exception:
                pass
            self.jlink.close()

    def get_hw_serial_number(self):
        if self.jlink is not None and self.jlink.opened():
            return self.jlink.serial_number
        return 0

    def hw_is_open(self):
        return self.jlink is not None and self.jlink.opened()

    def hw_write(self, data):
        if not self._ensure_jlink():
            self.err_cb(self._jlink_error + '\n')
            return
        self.jlink.rtt_write(0, data)

    def hw_read(self):
        if self.jlink is None or not self.rtt_is_start:
            return
        try:
            rtt_data = self.jlink.rtt_read(self.buffer_idx, self.read_size)
            if self.char_format == 'asc':
                rtt_data_str = ''.join([chr(v) for v in rtt_data])
                self.hw_data_handle(rtt_data_str)
            elif self.char_format == 'utf-8':
                if len(rtt_data) > 0:
                    self.bytes_data += bytes(rtt_data)
                    self.clk = int((6 / (self.rx_timeout * 1000)))
                else:
                    if self.clk != 0:
                        self.clk -= 1
                if self.clk == 0:
                    decoded_str = self.bytes_data.decode('utf-8', errors='ignore')
                    decoded_str = decoded_str.replace("\\n", "\n")
                    self.hw_data_handle(decoded_str)
                    self.bytes_data = b''
            elif self.char_format == 'gb2312':
                if len(rtt_data) > 0:
                    self.bytes_data += bytes(rtt_data)
                    self.clk = int((6 / (self.rx_timeout * 1000)))
                else:
                    if self.clk != 0:
                        self.clk -= 1
                if self.clk == 0:
                    decoded_str = self.bytes_data.decode('gb2312', errors='ignore')
                    decoded_str = decoded_str.replace("\\n", "\n")
                    self.hw_data_handle(decoded_str)
                    self.bytes_data = b''
            else:
                self.err_cb('J_Link: 不支持的数据格式%s.\n' % self.char_format)
        except Exception as e:
            self.err_cb('J_Link:%s\n' % e)


if __name__ == '__main__':
    pass
