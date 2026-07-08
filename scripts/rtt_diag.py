"""Quick RTT diagnostic: connect, wait for CB, dump status, read channel 0."""
import os
import sys
import time

import pylink
from pylink import library as pylink_library

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import config_manager
from bds.bds_jlink import (
    BDS_Jlink,
    DTCM_RTT_UP_BUF,
    RTT_CB_AUP0_PBUFFER_OFF,
    RTT_CB_AUP0_SIZE_OFF,
    RTT_CB_AUP0_WROFF_OFF,
    find_jlink_dll,
)


def load_cfg():
    return config_manager.load_config()


def main():
    cfg = load_cfg()
    addr, size = config_manager.parse_rtt_search_values(cfg.get('rtt_block_address'))
    chip = cfg['jk_chip'][0]

    dll = find_jlink_dll()
    lib = pylink_library.Library(dllpath=dll) if dll else pylink_library.Library()
    jlink = pylink.JLink(lib=lib)
    jlink.open()
    jlink.set_tif(pylink.enums.JLinkInterfaces.SWD)
    jlink.set_speed(cfg.get('jk_speed', 4000))
    jlink.connect(chip)

    hw = BDS_Jlink(lambda m: print(m, end=''), lambda m: print(m, end=''), chip=chip)
    hw.jlink = jlink
    hw._enable_stm32h7_debug()

    if cfg.get('jk_con_reset', True):
        jlink.reset(ms=10, halt=True)
        hw._clear_rtt_control_block(addr)
        jlink.restart(skip_breakpoints=True)
        print('CPU running, waiting for RTT init...')
        if not hw._wait_for_rtt_ready(addr, timeout_s=8.0):
            print('TIMEOUT: RTT CB not valid')
            jlink.close()
            return 1
    elif not hw._is_rtt_cb_valid(addr):
        print('RTT CB not valid on running target')
        jlink.close()
        return 1

    hw._start_rtt(addr, addr, size)
    pbuf = jlink.memory_read32(addr + RTT_CB_AUP0_PBUFFER_OFF, 1)[0]
    bufsize = jlink.memory_read32(addr + RTT_CB_AUP0_SIZE_OFF, 1)[0]
    wr_off = jlink.memory_read32(addr + RTT_CB_AUP0_WROFF_OFF, 1)[0]
    print('CB @ 0x%08X: pBuffer=0x%08X size=%u WrOff=%u (expect pBuffer=0x%08X)' % (
        addr, pbuf, bufsize, wr_off, DTCM_RTT_UP_BUF))

    print('Polling RTT channel 0 for 10s...')
    for _ in range(200):
        data = jlink.rtt_read(0, 4096)
        if data:
            text = bytes(data).decode('utf-8', errors='replace')
            sys.stdout.write(text)
            sys.stdout.flush()
        time.sleep(0.05)

    jlink.rtt_stop()
    jlink.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
