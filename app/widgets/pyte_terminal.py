import pyte
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPalette, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QPlainTextEdit

PYTE_FG_COLORS = {
    'black': '#000000',
    'red': '#CD3131',
    'green': '#0DBC79',
    'brown': '#E5E510',
    'blue': '#2472C8',
    'magenta': '#BC3FBC',
    'cyan': '#11A8CD',
    'white': '#E5E5E5',
    'brightblack': '#666666',
    'brightred': '#F14C4C',
    'brightgreen': '#23D18B',
    'brightbrown': '#F5F543',
    'brightblue': '#3B8EEA',
    'brightmagenta': '#D670D6',
    'brightcyan': '#29B8DB',
    'brightwhite': '#FFFFFF',
}

PYTE_BG_COLORS = {
    'black': '#000000',
    'red': '#CD3131',
    'green': '#0DBC79',
    'brown': '#E5E510',
    'blue': '#2472C8',
    'magenta': '#BC3FBC',
    'cyan': '#11A8CD',
    'white': '#E5E5E5',
    'brightblack': '#666666',
    'brightred': '#F14C4C',
    'brightgreen': '#23D18B',
    'brightbrown': '#F5F543',
    'brightblue': '#3B8EEA',
    'brightmagenta': '#D670D6',
    'brightcyan': '#29B8DB',
    'brightwhite': '#FFFFFF',
}


class PyteTerminalWidget(QPlainTextEdit):
    MAX_HISTORY_LINES = 10000
    FIXED_COLS = 120

    bytes_send_requested = Signal(object)
    line_committed = Signal(str)

    def __init__(self, font_family='Consolas', font_size=12, default_text_color='#C0C0C0', default_bg_color='#0C0C0C', parent=None):
        super().__init__(parent)
        self.setObjectName('logTerminal')
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setFont(QFont(font_family, int(font_size)))
        self.setReadOnly(False)
        self.setTextInteractionFlags(Qt.TextInteractionFlag.TextEditorInteraction)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setInputMethodHints(Qt.InputMethodHint.ImhNoAutoUppercase | Qt.InputMethodHint.ImhNoPredictiveText)
        self.document().setUndoRedoEnabled(False)
        self.setCursorWidth(0)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._default_text_color = default_text_color
        self._default_bg_color = default_bg_color
        self._follow_output = True
        self._paused = False
        self._dirty = False
        self._line_break = '\n'
        self._input_buffer = ''
        self._local_echo = True
        self._composing = False
        self._cols = self.FIXED_COLS
        self._rows = 30
        self._cursor_visible = True
        self._screen = pyte.HistoryScreen(self._cols, self._rows, history=self.MAX_HISTORY_LINES)
        self._stream = pyte.ByteStream(self._screen)
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(40)
        self._refresh_timer.timeout.connect(self._refresh_if_dirty)
        self._refresh_timer.start()
        self._cursor_blink_timer = QTimer(self)
        self._cursor_blink_timer.setInterval(500)
        self._cursor_blink_timer.timeout.connect(self._toggle_cursor_blink)
        self._cursor_blink_timer.start()
        self.verticalScrollBar().valueChanged.connect(self._on_scroll)
        self.apply_theme_colors(default_text_color, default_bg_color)

    def apply_theme_colors(self, fg_color, bg_color):
        self._default_text_color = fg_color
        self._default_bg_color = bg_color
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(bg_color))
        palette.setColor(QPalette.ColorRole.Text, QColor(fg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        self._dirty = True

    def set_line_break(self, line_break):
        self._line_break = line_break or ''

    def set_local_echo(self, enabled):
        self._local_echo = bool(enabled)

    def local_echo(self):
        return self._local_echo

    def set_paused(self, paused):
        self._paused = paused
        if not paused and self._follow_output:
            self.scroll_to_bottom()

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._follow_output = True

    def should_auto_scroll(self):
        return not self._paused and self._follow_output

    def clear_terminal(self):
        self._screen.reset()
        self._stream = pyte.ByteStream(self._screen)
        self._input_buffer = ''
        self.clear()
        self._dirty = False

    def append_plain(self, text):
        self.feed_text(text)

    def feed_text(self, text):
        if not text:
            return
        self.feed_bytes(text.encode('utf-8', errors='replace'))

    def feed_bytes(self, data):
        if not data:
            return
        self._stream.feed(self._normalize_newlines(data))
        self._dirty = True

    def _normalize_newlines(self, data):
        if b'\n' not in data:
            return data
        out = bytearray()
        for index, byte in enumerate(data):
            if byte == 0x0A and (index == 0 or data[index - 1] != 0x0D):
                out.extend(b'\r\n')
            else:
                out.append(byte)
        return bytes(out)

    def get_all_text(self):
        return self._build_plain_text()

    def select_all_text(self):
        self.selectAll()
        self._follow_output = False

    def copy_text(self):
        cursor = self.textCursor()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()
            if start == 0 and end >= max(self.document().characterCount() - 1, 0):
                text = self.get_all_text()
            else:
                text = cursor.selectedText().replace('\u2029', '\n')
        else:
            text = self.get_all_text()
        if text:
            QGuiApplication.clipboard().setText(text)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_screen()

    def showEvent(self, event):
        super().showEvent(event)
        self._resize_screen()

    def _resize_screen(self):
        metrics = self.fontMetrics()
        line_height = max(metrics.lineSpacing(), 1)
        rows = max(self.viewport().height() // line_height, 3)
        if rows == self._rows:
            return
        self._rows = rows
        self._screen.resize(rows, self._cols)
        self._dirty = True

    def _toggle_cursor_blink(self):
        if self.textCursor().hasSelection():
            return
        self._cursor_visible = not self._cursor_visible
        self._dirty = True

    def _on_scroll(self, value):
        if self._paused:
            return
        if self.textCursor().hasSelection():
            self._follow_output = False
            return
        scrollbar = self.verticalScrollBar()
        self._follow_output = value >= scrollbar.maximum()

    def _refresh_if_dirty(self):
        if not self._dirty:
            return
        if QGuiApplication.mouseButtons() & Qt.MouseButton.LeftButton:
            return
        self._dirty = False
        self._render_screen()

    def _render_screen(self):
        selection = self.textCursor()
        had_selection = selection.hasSelection()
        start = selection.selectionStart()
        end = selection.selectionEnd()
        old_count = self.document().characterCount()
        select_all = had_selection and start == 0 and end >= max(old_count - 1, 0)

        cursor = QTextCursor(self.document())
        cursor.beginEditBlock()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.removeSelectedText()

        default_format = self._default_format()
        width = self._screen.columns
        history_count = len(self._screen.history.top)
        for index, history_line in enumerate(self._screen.history.top):
            self._append_line(cursor, history_line, default_format, index, history_count)
        last_row = self._screen.lines - 1
        while last_row >= 0 and self._line_plain_text(self._screen.buffer[last_row], width) == '':
            last_row -= 1
        for y in range(last_row + 1):
            self._append_line(cursor, self._screen.buffer[y], default_format, history_count + y, history_count)

        cursor.endEditBlock()

        new_count = self.document().characterCount()
        if select_all:
            self.selectAll()
            self._follow_output = False
        elif had_selection:
            restored = self.textCursor()
            last = max(new_count - 1, 0)
            restored.setPosition(min(start, last))
            restored.setPosition(min(end, last), QTextCursor.MoveMode.KeepAnchor)
            self.setTextCursor(restored)
            self._follow_output = False
        elif not self._paused and self._follow_output:
            self.scroll_to_bottom()

    def mousePressEvent(self, event):
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.LeftButton:
            self._follow_output = False
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.NoButton:
            event.accept()
            return
        super().mouseMoveEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self._cursor_visible = True
        self._dirty = True

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self._dirty = True

    def _line_char(self, line, x):
        if isinstance(line, (list, tuple)):
            return line[x]
        return line.get(x, self._screen.default_char)

    def _append_line(self, cursor, line, default_format, absolute_y, history_count):
        width = self._screen.columns
        chars = []
        for x in range(width):
            chars.append(self._line_char(line, x))
        while chars and chars[-1].data == ' ':
            end = len(chars) - 1
            if absolute_y == history_count + self._screen.cursor.y and end == self._screen.cursor.x:
                break
            chars.pop()
        for x, char in enumerate(chars):
            is_cursor = (
                self._cursor_visible
                and not self._screen.cursor.hidden
                and absolute_y == history_count + self._screen.cursor.y
                and x == self._screen.cursor.x
            )
            if is_cursor:
                fmt = self._cursor_format(char, default_format)
            else:
                fmt = self._char_format(char, default_format)
            cursor.setCharFormat(fmt)
            cursor.insertText(char.data if char.data else ' ')
        if (
            self._cursor_visible
            and not self._screen.cursor.hidden
            and absolute_y == history_count + self._screen.cursor.y
            and self._screen.cursor.x >= len(chars)
        ):
            fmt = self._cursor_format(self._screen.default_char, default_format)
            cursor.setCharFormat(fmt)
            cursor.insertText(' ')
        cursor.setCharFormat(default_format)
        cursor.insertText('\n')

    def _cursor_format(self, char, default_format):
        fmt = QTextCharFormat(default_format)
        fg = self._resolve_color(char.fg, self._default_text_color, PYTE_FG_COLORS)
        bg = self._resolve_color(char.bg, self._default_bg_color, PYTE_BG_COLORS)
        if char.reverse:
            fg, bg = bg, fg
        else:
            fg, bg = bg, fg
        fmt.setForeground(QColor(fg))
        fmt.setBackground(QColor(bg))
        return fmt

    def _char_format(self, char, default_format):
        fmt = QTextCharFormat(default_format)
        fg = self._resolve_color(char.fg, self._default_text_color, PYTE_FG_COLORS)
        bg = self._resolve_color(char.bg, self._default_bg_color, PYTE_BG_COLORS)
        if char.reverse:
            fg, bg = bg, fg
        fmt.setForeground(QColor(fg))
        fmt.setBackground(QColor(bg))
        if char.bold:
            font = fmt.font()
            font.setBold(True)
            fmt.setFont(font)
        if char.italics:
            font = fmt.font()
            font.setItalic(True)
            fmt.setFont(font)
        if char.underscore:
            fmt.setFontUnderline(True)
        if char.strikethrough:
            fmt.setFontStrikeOut(True)
        return fmt

    def _resolve_color(self, name, default, palette):
        if not name or name == 'default':
            return default
        return palette.get(name, default)

    def _default_format(self):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(self._default_text_color))
        fmt.setBackground(QColor(self._default_bg_color))
        return fmt

    def _build_plain_text(self):
        lines = []
        width = self._screen.columns
        for history_line in self._screen.history.top:
            lines.append(self._line_plain_text(history_line, width))
        last_row = self._screen.lines - 1
        while last_row >= 0 and self._line_plain_text(self._screen.buffer[last_row], width) == '':
            last_row -= 1
        for y in range(last_row + 1):
            lines.append(self._line_plain_text(self._screen.buffer[y], width))
        return '\n'.join(lines)

    def _line_plain_text(self, line, width):
        chars = []
        for x in range(width):
            chars.append(self._line_char(line, x).data)
        return ''.join(chars).rstrip()

    def _line_ending_bytes(self):
        ending = self._line_break
        if ending is None:
            return [13]
        if ending == '':
            return []
        return list(ending.encode('utf-8'))

    def _send_payload(self, payload, echo_text=None):
        if payload:
            self.bytes_send_requested.emit(payload)
        if self._local_echo and echo_text:
            self.feed_text(echo_text)
        self._follow_output = True

    def _send_user_text(self, text):
        if not text:
            return
        normalized = text.replace('\r\n', '\n').replace('\r', '\n')
        parts = normalized.split('\n')
        for index, part in enumerate(parts):
            if part:
                self._input_buffer += part
                self._send_payload(list(part.encode('utf-8')), part if self._local_echo else None)
            if index != len(parts) - 1:
                self._commit_input_line()

    def _pyte_cursor_rect(self):
        history_count = len(self._screen.history.top)
        line = max(history_count + self._screen.cursor.y, 0)
        col = max(self._screen.cursor.x, 0)
        block = self.document().findBlockByNumber(line)
        cursor = QTextCursor(self.document())
        if block.isValid():
            cursor = QTextCursor(block)
            if col > 0:
                cursor.movePosition(
                    QTextCursor.MoveOperation.Right,
                    QTextCursor.MoveMode.MoveAnchor,
                    min(col, block.length()),
                )
        else:
            cursor.movePosition(QTextCursor.MoveOperation.End)
        rect = self.cursorRect(cursor)
        if rect.width() < 2:
            rect.setWidth(max(self.fontMetrics().horizontalAdvance('M'), 8))
        if rect.height() < 2:
            rect.setHeight(self.fontMetrics().height())
        return rect

    def inputMethodQuery(self, query):
        query = Qt.InputMethodQuery(query)
        if query == Qt.InputMethodQuery.ImEnabled:
            return True
        if query in (Qt.InputMethodQuery.ImCursorRectangle, Qt.InputMethodQuery.ImAnchorRectangle):
            return self._pyte_cursor_rect()
        if query == Qt.InputMethodQuery.ImCursorPosition:
            return len(self._input_buffer)
        if query == Qt.InputMethodQuery.ImSurroundingText:
            return self._input_buffer
        if query == Qt.InputMethodQuery.ImCurrentSelection:
            return ''
        if query == Qt.InputMethodQuery.ImAnchorPosition:
            return len(self._input_buffer)
        return super().inputMethodQuery(query)

    def inputMethodEvent(self, event):
        preedit = event.preeditString()
        commit = event.commitString()
        if commit:
            self._send_user_text(commit)
        self._composing = bool(preedit)
        if commit or preedit:
            event.accept()
        else:
            super().inputMethodEvent(event)
        im = QGuiApplication.inputMethod()
        if im is not None:
            im.update(Qt.InputMethodQuery.ImCursorRectangle)

    def insertFromMimeData(self, source):
        if source is not None and source.hasText():
            self._send_user_text(source.text())
            return
        super().insertFromMimeData(source)

    def canInsertFromMimeData(self, source):
        return source is not None and source.hasText()

    def paste_text(self, text=None):
        if text is None:
            text = QGuiApplication.clipboard().text()
        self._send_user_text(text)

    def _commit_input_line(self):
        line = self._input_buffer
        self._input_buffer = ''
        self.line_committed.emit(line)
        ending = self._line_ending_bytes()
        echo = None
        if self._local_echo:
            echo = '\r\n' if self._line_break == '\r\n' else '\n'
        self._send_payload(ending, echo)

    def keyPressEvent(self, event):
        key = event.key()
        ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
        if self._composing and not ctrl and key not in (
            Qt.Key.Key_Return,
            Qt.Key.Key_Enter,
            Qt.Key.Key_Escape,
            Qt.Key.Key_Backspace,
            Qt.Key.Key_Tab,
        ):
            event.accept()
            return
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
            self._composing = False
        self._handle_key(event)
        event.accept()

    def _handle_key(self, event):
        key = event.key()
        modifiers = event.modifiers()
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        alt = bool(modifiers & Qt.KeyboardModifier.AltModifier)

        if key in (Qt.Key.Key_Shift, Qt.Key.Key_Control, Qt.Key.Key_Alt, Qt.Key.Key_Meta, Qt.Key.Key_AltGr):
            return

        if key == Qt.Key.Key_C and ctrl:
            if self.textCursor().hasSelection():
                self.copy_text()
            else:
                self._send_payload([3])
            return

        if key == Qt.Key.Key_A and ctrl:
            self.select_all_text()
            return

        if key == Qt.Key.Key_Insert and ctrl:
            self.copy_text()
            return

        if (key == Qt.Key.Key_V and ctrl) or (key == Qt.Key.Key_Insert and modifiers & Qt.KeyboardModifier.ShiftModifier):
            self.paste_text()
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter) or event.text() in ('\r', '\n'):
            self._commit_input_line()
            return

        if key == Qt.Key.Key_Backspace:
            if self._input_buffer:
                self._input_buffer = self._input_buffer[:-1]
            echo = '\b \b' if self._local_echo else None
            self._send_payload([8], echo)
            return

        if key in (Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
            self._send_payload([9])
            return

        if key == Qt.Key.Key_Escape:
            self._send_payload([27])
            return

        ansi_keys = {
            Qt.Key.Key_Up: [27, 91, 65],
            Qt.Key.Key_Down: [27, 91, 66],
            Qt.Key.Key_Right: [27, 91, 67],
            Qt.Key.Key_Left: [27, 91, 68],
            Qt.Key.Key_Home: [27, 91, 72],
            Qt.Key.Key_End: [27, 91, 70],
            Qt.Key.Key_Delete: [27, 91, 51, 126],
            Qt.Key.Key_PageUp: [27, 91, 53, 126],
            Qt.Key.Key_PageDown: [27, 91, 54, 126],
        }
        if key in ansi_keys:
            self._send_payload(ansi_keys[key])
            return

        if ctrl and not alt and Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            self._send_payload([key - Qt.Key.Key_A + 1])
            return

        text = event.text()
        if text and text >= ' ' and not alt:
            self._send_user_text(text)
