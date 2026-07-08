from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class FindDialog(QDialog):
    find_requested = Signal(str, str)

    def __init__(self, search_history=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('查找内容')
        self.setModal(False)
        layout = QVBoxLayout(self)

        row = QHBoxLayout()
        self.find_combo = QComboBox()
        self.find_combo.setEditable(True)
        self.find_combo.setMinimumWidth(420)
        if search_history:
            self.find_combo.addItems(search_history)
        row.addWidget(self.find_combo, stretch=1)

        btn_col = QVBoxLayout()
        self.next_btn = QPushButton('查找下一个')
        self.next_btn.clicked.connect(lambda: self._emit_find('next'))
        btn_col.addWidget(self.next_btn)
        self.prev_btn = QPushButton('查找上一个')
        self.prev_btn.clicked.connect(lambda: self._emit_find('prev'))
        btn_col.addWidget(self.prev_btn)
        row.addLayout(btn_col)
        layout.addLayout(row)

    def _emit_find(self, direction):
        self.find_requested.emit(self.find_combo.currentText(), direction)

    def add_history_item(self, keyword):
        if keyword and self.find_combo.findText(keyword) < 0:
            self.find_combo.insertItem(0, keyword)
