import os
import sys

import bds.bds_serial as bds_ser
import config_manager
from app.qt import QApplication

from app.fonts import apply_application_fonts, resolve_font_settings
from app.main_window import MainWindow
from app.theme_loader import apply_theme


def create_application():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName('RTT_T2')
    app.setOrganizationName('BDS')
    return app


def run():
    config_manager.initialize_app_environment()
    js_cfg = config_manager.load_config()
    if bds_ser.sync_serial_config(js_cfg):
        config_manager.save_config(js_cfg)
    if 'search_history' not in js_cfg:
        js_cfg['search_history'] = []

    app = create_application()
    font_settings = resolve_font_settings(js_cfg)
    js_cfg['font'] = [font_settings.mono_family, font_settings.ui_family]
    js_cfg['font_size'] = str(font_settings.size)
    apply_application_fonts(app, font_settings)
    apply_theme(app, js_cfg, font_settings)

    window = MainWindow(js_cfg)
    window.show()
    return app.exec()
