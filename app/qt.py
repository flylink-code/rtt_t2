import os


if os.environ.get('RTT_QT_BINDING') != 'PySide2':
    from PySide6.QtCore import QEvent, QObject, QThread, QTimer, Qt, Signal
    from PySide6.QtGui import (
        QAction, QBrush, QColor, QFont, QFontDatabase, QGuiApplication, QIcon,
        QKeySequence, QPainter, QPalette, QPen, QPixmap, QShortcut,
        QTextCharFormat, QTextCursor,
    )
    from PySide6.QtWidgets import *
else:
    from PySide2.QtCore import QEvent, QObject, QThread, QTimer, Qt, Signal
    from PySide2.QtGui import (
        QAction, QBrush, QColor, QFont, QFontDatabase, QGuiApplication, QIcon,
        QKeySequence, QPainter, QPalette, QPen, QPixmap, QShortcut,
        QTextCharFormat, QTextCursor,
    )
    from PySide2.QtWidgets import *
