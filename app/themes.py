from dataclasses import dataclass

THEME_DARK = 'dark'
THEME_LIGHT = 'light'
THEMES = (THEME_DARK, THEME_LIGHT)

THEME_LABELS = {
    THEME_DARK: '暗色（Xterm）',
    THEME_LIGHT: '亮色（Xterm）',
}


@dataclass(frozen=True)
class ThemeColors:
    terminal_fg: str
    terminal_bg: str
    search_all_bg: str
    search_all_fg: str
    search_current_bg: str
    search_current_fg: str


THEME_COLORS = {
    THEME_DARK: ThemeColors(
        terminal_fg='#C0C0C0',
        terminal_bg='#0C0C0C',
        search_all_bg='#4D4D00',
        search_all_fg='#FFFFAA',
        search_current_bg='#0078D4',
        search_current_fg='#FFFFFF',
    ),
    THEME_LIGHT: ThemeColors(
        terminal_fg='#1A1A1A',
        terminal_bg='#FFFFFF',
        search_all_bg='#FFF4B0',
        search_all_fg='#1A1A1A',
        search_current_bg='#316AC5',
        search_current_fg='#FFFFFF',
    ),
}


def normalize_theme(name):
    if name in THEMES:
        return name
    return THEME_DARK


def get_theme_colors(theme_name):
    return THEME_COLORS[normalize_theme(theme_name)]
