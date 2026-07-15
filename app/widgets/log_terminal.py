from app.qt import QColor, QFont, QPalette, QPlainTextEdit, QTextCharFormat, QTextCursor, Qt, QTimer

from app.services.log_service import LEGACY_DEFAULT_LOG_COLOR


def _color_from_int(value):
    return QColor('#%06X' % (value & 0xFFFFFF))


class LogTerminalWidget(QPlainTextEdit):
    MAX_BLOCKS = 50000

    def __init__(self, font_family='Consolas', font_size=12, default_text_color='#C0C0C0', default_bg_color='#0C0C0C', parent=None):
        super().__init__(parent)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont(font_family, int(font_size)))
        self.setObjectName('logTerminal')
        self._default_text_color = default_text_color
        self._default_bg_color = default_bg_color
        self._follow_output = True
        self._paused = False
        self._pending_segments = []
        self._flush_timer = QTimer(self)
        self._flush_timer.setInterval(40)
        self._flush_timer.timeout.connect(self._flush_pending)
        self._flush_timer.start()
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.setReadOnly(True)
        self.apply_theme_colors(default_text_color, default_bg_color)

    def apply_theme_colors(self, fg_color, bg_color):
        self._default_text_color = fg_color
        self._default_bg_color = bg_color
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
        palette.setColor(QPalette.ColorRole.Text, QColor(fg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def set_default_text_color(self, color):
        self.apply_theme_colors(color, self._default_bg_color)

    def set_paused(self, paused):
        self._paused = paused
        if not paused and self._follow_output:
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._follow_output = True

    def clear_terminal(self):
        self.clear()
        self._pending_segments.clear()

    def append_plain(self, text):
        if not text:
            return
        self._pending_segments.append((text, None))

    def append_colored_segments(self, segments):
        if not segments:
            return
        self._pending_segments.extend(segments)

    def append_log_result(self, result):
        if result is None:
            return
        kind = result.get('kind')
        if kind == 'plain' or kind == 'error':
            self.append_plain(result.get('text', ''))
        elif kind == 'colored':
            self.append_colored_segments(result.get('segments', []))

    def _segment_color(self, color):
        if color is None or color in (0, LEGACY_DEFAULT_LOG_COLOR):
            return QColor(self._default_text_color)
        return _color_from_int(color)

    def _on_scroll(self, value):
        if self._paused:
            return
        scrollbar = self.verticalScrollBar()
        self._follow_output = value >= scrollbar.maximum()

    def _default_format(self):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._default_text_color))
        return fmt

    def _flush_pending(self):
        if not self._pending_segments:
            return

        cursor = QTextCursor(self.document())
        cursor.movePosition(QTextCursor.MoveOperation.End)
        default_format = self._default_format()

        while self._pending_segments:
            text, color = self._pending_segments.pop(0)
            if not text:
                continue
            fmt = QTextCharFormat()
            if color is None:
                fmt = default_format
            else:
                fmt.setForeground(self._segment_color(color))
            cursor.setCharFormat(fmt)
            cursor.insertText(text)

        self._trim_blocks()
        if not self._paused and self._follow_output:
            self.scroll_to_bottom()

    def _trim_blocks(self):
        if self.document().blockCount() <= self.MAX_BLOCKS:
            return
        trim_cursor = QTextCursor(self.document())
        trim_cursor.movePosition(QTextCursor.MoveOperation.Start)
        trim_cursor.movePosition(
            QTextCursor.MoveOperation.Down,
            QTextCursor.MoveMode.KeepAnchor,
            self.document().blockCount() - self.MAX_BLOCKS,
        )
        trim_cursor.removeSelectedText()

    def get_all_text(self):
        self._flush_pending()
        return self.toPlainText()

    def should_auto_scroll(self):
        return not self._paused and self._follow_output
