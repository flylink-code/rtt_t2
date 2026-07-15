from app.qt import (
    Qt,
    Signal,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import config_manager
from app.services.session_service import send_payload


class CustomCommandsDialog(QDialog):
    commands_changed = Signal()
    command_send_requested = Signal(dict)

    def __init__(self, js_cfg, hw_obj, parent=None):
        super().__init__(parent)
        self.js_cfg = js_cfg
        self.hw_obj = hw_obj
        self._commands = [dict(item) for item in js_cfg.get('custom_commands', [])]
        self.setWindowTitle('自定义命令')
        self.setMinimumSize(640, 420)
        self._build_ui()
        self._reload_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        hint = QLabel('维护常用命令快捷发送。ASC 类型发送时会自动追加配置中的换行符。')
        hint.setWordWrap(True)
        layout.addWidget(hint)

        body = QHBoxLayout()
        self.command_list = QListWidget()
        self.command_list.currentRowChanged.connect(self._on_row_changed)
        body.addWidget(self.command_list, stretch=1)

        form_host = QWidget()
        form_layout = QFormLayout(form_host)
        self.name_edit = QLineEdit()
        self.content_edit = QPlainTextEdit()
        self.content_edit.setFixedHeight(90)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['ASC', 'HEX'])
        form_layout.addRow('名称', self.name_edit)
        form_layout.addRow('内容', self.content_edit)
        form_layout.addRow('类型', self.type_combo)
        body.addWidget(form_host, stretch=2)
        layout.addLayout(body)

        row = QHBoxLayout()
        self.add_btn = QPushButton('新增')
        self.add_btn.clicked.connect(self._add_command)
        self.delete_btn = QPushButton('删除')
        self.delete_btn.clicked.connect(self._delete_command)
        self.apply_btn = QPushButton('保存当前')
        self.apply_btn.clicked.connect(self._apply_current)
        self.send_btn = QPushButton('发送选中')
        self.send_btn.setObjectName('primaryButton')
        self.send_btn.clicked.connect(self._send_selected)
        for btn in (self.add_btn, self.delete_btn, self.apply_btn, self.send_btn):
            row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.accept)
        close_btn = buttons.button(QDialogButtonBox.StandardButton.Close)
        if close_btn is not None:
            close_btn.setText('关闭')
        layout.addWidget(buttons)

    def _get_content_text(self):
        return self.content_edit.toPlainText()

    def _set_content_text(self, text):
        self.content_edit.setPlainText(text)

    def _reload_list(self):
        self.command_list.blockSignals(True)
        self.command_list.clear()
        for command in self._commands:
            self.command_list.addItem(QListWidgetItem(command.get('name', '未命名')))
        self.command_list.blockSignals(False)
        if self._commands:
            self.command_list.setCurrentRow(0)
        else:
            self._clear_form()

    def _clear_form(self):
        self.name_edit.clear()
        self._set_content_text('')
        self.type_combo.setCurrentText('ASC')

    def _on_row_changed(self, row):
        if row < 0 or row >= len(self._commands):
            self._clear_form()
            return
        command = self._commands[row]
        self.name_edit.setText(command.get('name', ''))
        self._set_content_text(command.get('content', ''))
        self.type_combo.setCurrentText(command.get('tx_type', 'ASC'))

    def _current_form_command(self):
        name = self.name_edit.text().strip()
        if not name:
            raise ValueError('请填写命令名称')
        return {
            'name': name,
            'content': self._get_content_text(),
            'tx_type': self.type_combo.currentText(),
        }

    def _add_command(self):
        try:
            command = self._current_form_command()
        except ValueError as exc:
            QMessageBox.warning(self, '提示', str(exc))
            return
        self._commands.append(command)
        self._persist()
        self._reload_list()
        self.command_list.setCurrentRow(len(self._commands) - 1)

    def _apply_current(self):
        row = self.command_list.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请先选择或新增一条命令')
            return
        try:
            self._commands[row] = self._current_form_command()
        except ValueError as exc:
            QMessageBox.warning(self, '提示', str(exc))
            return
        self._persist()
        self._reload_list()
        self.command_list.setCurrentRow(row)

    def _delete_command(self):
        row = self.command_list.currentRow()
        if row < 0:
            return
        self._commands.pop(row)
        self._persist()
        self._reload_list()

    def _send_selected(self):
        row = self.command_list.currentRow()
        if row < 0:
            QMessageBox.information(self, '提示', '请选择要发送的命令')
            return
        self._send_command(self._commands[row])

    def _send_command(self, command):
        if not self.hw_obj.hw_is_open():
            QMessageBox.warning(self, '提示', '请先连接硬件')
            return
        sent, message, ok = send_payload(
            self.hw_obj,
            self.js_cfg,
            command.get('content', ''),
            command.get('tx_type', 'ASC'),
            save_history=False,
        )
        if not ok:
            QMessageBox.warning(self, '发送错误', message or '发送失败')
            return
        self.command_send_requested.emit(command)
        self.commands_changed.emit()

    def _persist(self):
        self.js_cfg['custom_commands'] = [dict(item) for item in self._commands]
        config_manager.save_config(self.js_cfg)
        self.commands_changed.emit()
