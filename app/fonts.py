from dataclasses import dataclass

from PySide6.QtGui import QFont, QFontDatabase

MONO_FONT_CANDIDATES = (
    'Cascadia Mono',
    'Cascadia Code',
    'JetBrains Mono',
    'Sarasa Mono SC',
    'Microsoft YaHei Mono',
    'Consolas',
)

UI_FONT_CANDIDATES = (
    'Segoe UI Variable Text',
    'Segoe UI',
    'Microsoft YaHei UI',
)


@dataclass(frozen=True)
class FontSettings:
    ui_family: str
    mono_family: str
    size: int


def _pick_available_family(candidates):
    available = set(QFontDatabase.families())
    for family in candidates:
        if family and family in available:
            return family
    return candidates[-1]


def resolve_font_settings(js_cfg):
    configured = js_cfg.get('font', [])
    mono_pref = configured[0] if len(configured) > 0 else None
    ui_pref = configured[1] if len(configured) > 1 else None

    mono_candidates = [mono_pref] if mono_pref else []
    mono_candidates.extend(MONO_FONT_CANDIDATES)

    ui_candidates = [ui_pref] if ui_pref else []
    ui_candidates.extend(UI_FONT_CANDIDATES)

    size = int(js_cfg.get('font_size', 13))
    return FontSettings(
        ui_family=_pick_available_family(ui_candidates),
        mono_family=_pick_available_family(mono_candidates),
        size=size,
    )


def apply_application_fonts(app, font_settings):
    app.setFont(QFont(font_settings.ui_family, font_settings.size))


def build_stylesheet(content, font_settings):
    replacements = {
        '@UI_FONT@': font_settings.ui_family,
        '@MONO_FONT@': font_settings.mono_family,
        '@UI_SIZE@': str(font_settings.size),
    }
    for token, value in replacements.items():
        content = content.replace(token, value)
    return content
