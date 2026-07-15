from app.qt import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)


class FilterDialog(QDialog):
    def __init__(self, js_cfg, parent=None):
        super().__init__(parent)
        self.js_cfg = js_cfg
        self.setWindowTitle('日志过滤器')
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        tip = QLabel(
            '仅对日志模式生效。多个关键字用 && 连接，例如：TAG=DLOG&&TAG=BDS\n'
            '建议每个关键字长度 ≥ 3。勾选「取反」后只保留匹配行。'
        )
        tip.setWordWrap(True)
        layout.addWidget(tip)

        form = QFormLayout()
        self.filter_edit = QLineEdit(js_cfg.get('filter', ''))
        self.filter_edit.setPlaceholderText('例如：TAG=DLOG')
        self.filter_enable = QCheckBox('启用过滤器')
        self.filter_enable.setChecked(bool(js_cfg.get('filter_en', False)))
        self.filter_inverse = QCheckBox('取反（只保留匹配行）')
        self.filter_inverse.setChecked(bool(js_cfg.get('filter_inverse', False)))
        form.addRow('表达式', self.filter_edit)
        form.addRow('', self.filter_enable)
        form.addRow('', self.filter_inverse)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def apply_to_config(self):
        self.js_cfg['filter'] = self.filter_edit.text().strip()
        self.js_cfg['filter_en'] = self.filter_enable.isChecked()
        self.js_cfg['filter_inverse'] = self.filter_inverse.isChecked()
