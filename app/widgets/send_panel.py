from app.qt import (
    Signal,
    QFont,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.services.session_service import get_line_break_display


class SendPanel(QWidget):
    send_requested = Signal()
    history_delete_requested = Signal()

    def __init__(self, js_cfg, font_family='Consolas', font_size=12, parent=None):
        super().__init__(parent)
        self._history_index = 0
        self.setObjectName('sendPanel')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        input_row = QHBoxLayout()
        self.input_edit = QPlainTextEdit()
        self.input_edit.setObjectName('sendInput')
        self.input_edit.setFont(QFont(font_family, int(font_size)))
        self.input_edit.setFixedHeight(90)
        self.input_edit.setPlaceholderText('输入要发送的数据，Enter 发送，Ctrl+Enter 换行')
        input_row.addWidget(self.input_edit, stretch=1)

        side_col = QVBoxLayout()
        self.send_btn = QPushButton('发送')
        self.send_btn.setObjectName('primaryButton')
        self.send_btn.clicked.connect(self.send_requested.emit)
        side_col.addWidget(self.send_btn)

        self.tx_type_combo = QComboBox()
        self.tx_type_combo.addItems(['ASC', 'HEX'])
        side_col.addWidget(self.tx_type_combo)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel('编码'))
        self.char_format_combo = QComboBox()
        self.char_format_combo.addItems(['asc', 'utf-8', 'hex', 'gb2312'])
        self.char_format_combo.setCurrentText(js_cfg['char_format'])
        fmt_row.addWidget(self.char_format_combo)
        side_col.addLayout(fmt_row)

        lb_row = QHBoxLayout()
        lb_row.addWidget(QLabel('换行'))
        self.line_break_combo = QComboBox()
        self.line_break_combo.addItems([r'\n', r'\r\n', 'none'])
        self.line_break_combo.setCurrentText(get_line_break_display(js_cfg['line_break']))
        lb_row.addWidget(self.line_break_combo)
        side_col.addLayout(lb_row)
        side_col.addStretch()
        input_row.addLayout(side_col)
        layout.addLayout(input_row)

        history_row = QHBoxLayout()
        history_row.addWidget(QLabel('历史'))
        self.history_combo = QComboBox()
        self.history_combo.setEditable(False)
        self.set_history(js_cfg.get('user_input_data', []))
        self.history_combo.currentTextChanged.connect(self._on_history_selected)
        history_row.addWidget(self.history_combo, stretch=1)
        self.delete_history_btn = QPushButton('删除当前')
        self.delete_history_btn.clicked.connect(self.history_delete_requested.emit)
        history_row.addWidget(self.delete_history_btn)
        layout.addLayout(history_row)

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

    def get_input_text(self):
        return self.input_edit.toPlainText()

    def set_input_text(self, text):
        self.input_edit.setPlainText(text)

    def clear_input(self):
        self.input_edit.clear()

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
        item, index = self._history_from_direction(values, direction)
        if item is not None:
            self._history_index = index
            self.set_input_text(item)
        return item

    def _history_from_direction(self, values, direction):
        from app.services.session_service import get_next_history_item
        item, index = get_next_history_item(values, self._history_index, direction)
        return item, index

    def _on_history_selected(self, text):
        if text:
            self.set_input_text(text)
            values = [self.history_combo.itemText(i) for i in range(self.history_combo.count())]
            if text in values:
                self._history_index = values.index(text)
