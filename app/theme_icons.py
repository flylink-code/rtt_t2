import math

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap

from app.themes import THEME_DARK, normalize_theme


def make_theme_switch_icon(current_theme, size=18):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    center = size / 2.0
    if normalize_theme(current_theme) == THEME_DARK:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#F5C542'))
        radius = size * 0.28
        painter.drawEllipse(
            int(center - radius),
            int(center - radius),
            int(radius * 2),
            int(radius * 2),
        )
        painter.setPen(QPen(QColor('#F5C542'), 1.4))
        ray_inner = radius + 2
        ray_outer = radius + 4.5
        for index in range(8):
            angle = math.radians(index * 45)
            painter.drawLine(
                int(center + math.cos(angle) * ray_inner),
                int(center + math.sin(angle) * ray_inner),
                int(center + math.cos(angle) * ray_outer),
                int(center + math.sin(angle) * ray_outer),
            )
    else:
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor('#C8D0E0'))
        moon_radius = size * 0.34
        painter.drawEllipse(
            int(center - moon_radius),
            int(center - moon_radius),
            int(moon_radius * 2),
            int(moon_radius * 2),
        )
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        offset = size * 0.18
        painter.drawEllipse(
            int(center - moon_radius + offset),
            int(center - moon_radius - 1),
            int(moon_radius * 2),
            int(moon_radius * 2),
        )

    painter.end()
    return QIcon(pixmap)
