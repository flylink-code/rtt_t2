import os

from app.fonts import build_stylesheet, resolve_font_settings
from app.themes import normalize_theme


def load_stylesheet(app, theme_name, font_settings):
    style_dir = os.path.join(os.path.dirname(__file__), 'styles')
    style_path = os.path.join(style_dir, '%s.qss' % theme_name)
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as style_file:
            app.setStyleSheet(build_stylesheet(style_file.read(), font_settings))


def apply_theme(app, js_cfg, font_settings=None):
    if font_settings is None:
        font_settings = resolve_font_settings(js_cfg)
    theme = normalize_theme(js_cfg.get('ui_theme', 'dark'))
    load_stylesheet(app, theme, font_settings)
    return theme
