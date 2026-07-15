from app.qt import QColor, QMessageBox, QTextCharFormat, QTextCursor

from app.themes import THEME_DARK, get_theme_colors, normalize_theme


class QtTextSearcher:
    def __init__(self, text_widget, theme=THEME_DARK):
        self._text_widget = text_widget
        self._last_keyword = ''
        self._last_index = 0
        self._direction = 'next'
        self._theme = normalize_theme(theme)
        self._colors = get_theme_colors(self._theme)

    def set_theme(self, theme):
        self._theme = normalize_theme(theme)
        self._colors = get_theme_colors(self._theme)

    def set_text_widget(self, text_widget):
        self.reset()
        self._text_widget = text_widget

    def reset(self):
        self._last_keyword = ''
        self._last_index = 0
        self._direction = 'next'
        self._clear_highlight()

    def search(self, keyword, direction):
        if not keyword:
            return False

        document = self._text_widget.document()
        if keyword != self._last_keyword:
            self._clear_highlight()
            if not self._highlight_all(keyword):
                QMessageBox.information(self._text_widget, '查找', '没有找到目标字符串')
                return False
            self._last_keyword = keyword
            self._last_index = 0

        cursor = QTextCursor(document)
        if direction == 'next':
            if self._direction == 'prev':
                self._last_index += len(keyword)
            self._direction = 'next'
            cursor.setPosition(self._last_index)
            found = document.find(keyword, cursor)
            if found.isNull():
                cursor.setPosition(0)
                found = document.find(keyword, cursor)
        else:
            if self._direction == 'next' and self._last_index > 0:
                cursor.setPosition(max(0, self._last_index - len(keyword)))
            else:
                cursor.setPosition(max(0, document.characterCount() - 1))
            self._direction = 'prev'
            found = document.find(keyword, cursor, QTextCursor.FindFlag.FindBackward)

        if found.isNull():
            QMessageBox.information(self._text_widget, '查找', '未找到更多匹配信息!')
            return False

        self._last_index = found.selectionEnd()
        self._highlight_current(found.selectionStart(), found.selectionEnd())
        self._text_widget.setTextCursor(found)
        self._text_widget.ensureCursorVisible()
        return True

    def _clear_highlight(self):
        cursor = QTextCursor(self._text_widget.document())
        cursor.select(QTextCursor.SelectionType.Document)
        plain = QTextCharFormat()
        plain.setBackground(QColor('transparent'))
        cursor.setCharFormat(plain)

    def _highlight_all(self, keyword):
        document = self._text_widget.document()
        cursor = QTextCursor(document)
        found_any = False
        highlight = QTextCharFormat()
        highlight.setBackground(QColor(self._colors.search_all_bg))
        highlight.setForeground(QColor(self._colors.search_all_fg))
        while True:
            found = document.find(keyword, cursor)
            if found.isNull():
                break
            found_any = True
            found.mergeCharFormat(highlight)
            cursor.setPosition(found.selectionEnd())
        return found_any

    def _highlight_current(self, start, end):
        cursor = QTextCursor(self._text_widget.document())
        current = QTextCharFormat()
        current.setBackground(QColor(self._colors.search_current_bg))
        current.setForeground(QColor(self._colors.search_current_fg))
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        cursor.mergeCharFormat(current)
