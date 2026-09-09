from PySide6.QtCore import QEvent, QStringListModel, Qt, Signal
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.session_service import get_line_break_display


class CommandLineEdit(QLineEdit):
    send_requested = Signal()
    history_up = Signal()
    history_down = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._composing = False

    def inputMethodEvent(self, event):
        self._composing = bool(event.preeditString())
        super().inputMethodEvent(event)
        if event.commitString() and not event.preeditString():
            self._composing = False

    def _completer_visible(self):
        completer = self.completer()
        return completer is not None and completer.popup() is not None and completer.popup().isVisible()

    def keyPressEvent(self, event):
        if self._composing:
            super().keyPressEvent(event)
            return
        if self._completer_visible() and event.key() in (
            Qt.Key.Key_Up, Qt.Key.Key_Down, Qt.Key.Key_Return, Qt.Key.Key_Enter,
        ):
            super().keyPressEvent(event)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.send_requested.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Up:
            self.history_up.emit()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Down:
            self.history_down.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class SendPanel(QWidget):
    send_requested = Signal()
    history_delete_requested = Signal()
    mode_changed = Signal(str)

    def __init__(self, js_cfg, font_family='Consolas', font_size=12, parent=None):
        super().__init__(parent)
        self._history_index = -1
        self._browse_prefix = ''
        self._browsing = False
        self._multiline = js_cfg.get('send_panel_mode') == 'multiline'
        self.setObjectName('sendPanel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        command_bar = QWidget()
        command_bar.setObjectName('terminalInputBar')
        self._command_bar = command_bar
        command_row = QHBoxLayout(command_bar)
        command_row.setContentsMargins(6, 4, 6, 4)
        command_row.setSpacing(8)

        prompt = QLabel('>')
        prompt.setObjectName('terminalPrompt')
        command_row.addWidget(prompt)

        self.command_edit = CommandLineEdit()
        self.command_edit.setObjectName('terminalLineInput')
        self.command_edit.setFont(QFont(font_family, int(font_size)))
        self.command_edit.setPlaceholderText('输入命令，Enter 发送，↑↓ 翻历史，支持中文输入法')
        self.command_edit.setClearButtonEnabled(True)
        self.command_edit.send_requested.connect(self.send_requested)
        self.command_edit.history_up.connect(lambda: self.cycle_history('up'))
        self.command_edit.history_down.connect(lambda: self.cycle_history('down'))
        self.command_edit.textEdited.connect(self._on_command_edited)
        command_row.addWidget(self.command_edit, stretch=1)

        self.send_btn = QPushButton('发送')
        self.send_btn.setObjectName('primaryButton')
        self.send_btn.clicked.connect(self.send_requested.emit)
        command_row.addWidget(self.send_btn)
        layout.addWidget(command_bar)

        self.input_edit = QPlainTextEdit()
        self.input_edit.setObjectName('sendInput')
        self.input_edit.setFont(QFont(font_family, int(font_size)))
        self.input_edit.setFixedHeight(90)
        self.input_edit.setPlaceholderText('多行发送：Enter 发送，Ctrl+Enter 换行，↑↓ 翻历史')
        layout.addWidget(self.input_edit)

        options_row = QHBoxLayout()
        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems(['ASC', 'HEX'])
        options_row.addWidget(self.tx_type_combo)

        options_row.addWidget(QLabel('编码'))
        self.char_format_combo = QComboBox()
        self.char_format_combo.addItems(['asc', 'utf-8', 'hex', 'gb2312'])
        self.char_format_combo.setCurrentText(js_cfg['char_format'])
        options_row.addWidget(self.char_format_combo)

        options_row.addWidget(QLabel('换行'))
        self.line_break_combo = QComboBox()
        self.line_break_combo.addItems([r'\n', r'\r\n', 'none'])
        self.line_break_combo.setCurrentText(get_line_break_display(js_cfg['line_break']))
        options_row.addWidget(self.line_break_combo)

        self.multiline_check = QCheckBox('多行')
        self.multiline_check.setChecked(self._multiline)
        self.multiline_check.toggled.connect(self._on_multiline_toggled)
        options_row.addWidget(self.multiline_check)
        options_row.addStretch()

        options_row.addWidget(QLabel('历史'))
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.history_combo.setMinimumWidth(180)
        self._completer_model = QStringListModel(self)
        self._completer = QCompleter(self._completer_model, self)
        self._completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self._completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self._completer.setMaxVisibleItems(12)
        self.command_edit.setCompleter(self._completer)
        self.set_history(js_cfg.get('user_input_data', []))
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        options_row.addWidget(self.history_combo, stretch=1)
        self.delete_history_btn = QPushButton('删除当前')
        self.delete_history_btn.clicked.connect(self.history_delete_requested.emit)
        options_row.addWidget(self.delete_history_btn)
        layout.addLayout(options_row)

        self.input_edit.installEventFilter(self)
        self._apply_multiline_mode()

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self.insert_newline()
                    return True
                self.send_requested.emit()
                return True
            if event.key() == Qt.Key.Key_Up and self._cursor_on_first_line():
                self.cycle_history('up')
                return True
            if event.key() == Qt.Key.Key_Down and self._cursor_on_last_line():
                self.cycle_history('down')
                return True
        return super().eventFilter(obj, event)

    def _cursor_on_first_line(self):
        return self.input_edit.textCursor().blockNumber() == 0

    def _cursor_on_last_line(self):
        cursor = self.input_edit.textCursor()
        return cursor.blockNumber() == self.input_edit.document().blockCount() - 1

    def _on_multiline_toggled(self, checked):
        previous = self.get_input_text()
        self._multiline = bool(checked)
        self._apply_multiline_mode()
        self.set_input_text(previous)
        self.mode_changed.emit('multiline' if self._multiline else 'compact')
        self.focus_input()

    def _apply_multiline_mode(self):
        self.input_edit.setVisible(self._multiline)
        self.command_edit.setVisible(not self._multiline)
        self._command_bar.setVisible(True)

    def focus_input(self):
        if self._multiline:
            self.input_edit.setFocus(Qt.FocusReason.OtherFocusReason)
        else:
            self.command_edit.setFocus(Qt.FocusReason.OtherFocusReason)

    def set_history(self, values):
        current = self.history_combo.currentText()
        self.history_combo.blockSignals(True)
        self.history_combo.clear()
        self.history_combo.addItems(values)
        if current and current in values:
            self.history_combo.setCurrentText(current)
        elif values:
            self.history_combo.setCurrentIndex(0)
        self.history_combo.blockSignals(False)
        self._completer_model.setStringList(list(values or []))
        self._history_index = -1
        self._browsing = False

    def get_input_text(self):
        if self._multiline:
            return self.input_edit.toPlainText()
        return self.command_edit.text()

    def set_input_text(self, text):
        if self._multiline:
            self.input_edit.setPlainText(text)
            cursor = self.input_edit.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.input_edit.setTextCursor(cursor)
        else:
            self.command_edit.setText(text)
            self.command_edit.setCursorPosition(len(text))

    def clear_input(self):
        self.command_edit.clear()
        self.input_edit.clear()
        self._browsing = False
        self._history_index = -1
        self._browse_prefix = ''

    def get_tx_type(self):
        return self.tx_type_combo.currentText()

    def get_char_format(self):
        return self.char_format_combo.currentText()

    def get_line_break_display(self):
        return self.line_break_combo.currentText()

    def cycle_history(self, direction):
        values = [self.history_combo.itemText(i) for i in range(self.history_combo.count())]
        if not values:
            return None
        if not self._browsing:
            self._browse_prefix = self.get_input_text()
            self._browsing = True
            self._history_index = -1
        matches = [item for item in values if item.startswith(self._browse_prefix)]
        if not matches:
            matches = values
        if direction == 'up':
            self._history_index = min(self._history_index + 1, len(matches) - 1)
        else:
            self._history_index -= 1
            if self._history_index < 0:
                self._history_index = -1
                self.set_input_text(self._browse_prefix)
                return self._browse_prefix
        item = matches[self._history_index]
        self.set_input_text(item)
        return item

    def _on_command_edited(self, _text):
        self._browsing = False
        self._history_index = -1

    def _on_history_selected(self, text):
        if text:
            self.set_input_text(text)
            values = [self.history_combo.itemText(i) for i in range(self.history_combo.count())]
            if text in values:
                self._history_index = values.index(text)
                self._browsing = True
                self._browse_prefix = ''

    def insert_newline(self):
        if not self._multiline:
            return
        cursor = self.input_edit.textCursor()
        cursor.insertText('\n')
        self.input_edit.setTextCursor(cursor)
