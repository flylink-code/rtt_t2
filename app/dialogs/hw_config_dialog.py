import bds.bds_serial as bds_ser
import config_manager
from app.chip_catalog import detect_chip_vendor, get_chip_catalog, is_chip_header, iter_sorted_vendors
from app.services.session_service import extract_and_convert_hex
from app.themes import THEME_DARK, THEME_LABELS, THEMES, normalize_theme
from app.qt import (
    QTimer,
    Qt,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QRadioButton,
    QVBoxLayout,
)


class HwConfigDialog(QDialog):
    def __init__(self, js_cfg, parent=None):
        super().__init__(parent)
        self.js_cfg = js_cfg
        self.com_des_list = []
        self.com_name_list = []
        self.setWindowTitle('硬件接口配置')
        self.setMinimumWidth(720)
        self._build_ui()
        self._hotplug_timer = QTimer(self)
        self._hotplug_timer.timeout.connect(self._detect_serial_hotplug)
        self._hotplug_timer.start(1000)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        connection_group = QGroupBox('连接参数')
        connection_layout = QVBoxLayout(connection_group)

        iface_row = QHBoxLayout()
        self.jk_radio = QRadioButton('J-Link')
        self.ser_radio = QRadioButton('串口')
        iface_row.addWidget(self.jk_radio)
        iface_row.addWidget(self.ser_radio)
        iface_row.addStretch()
        connection_layout.addLayout(iface_row)

        if self.js_cfg.get('hw_sel', '1') == '1':
            self.jk_radio.setChecked(True)
        else:
            self.ser_radio.setChecked(True)

        jk_box = QGroupBox('J-Link 参数')
        jk_form = QFormLayout(jk_box)
        self.chip_combo = QComboBox()
        self._populate_chip_combo()
        self.jk_sn_edit = QLineEdit()
        self.jk_sn_edit.setReadOnly(True)
        self.jk_speed_edit = QLineEdit(str(self.js_cfg['jk_speed']))
        self.jk_reset_check = QCheckBox('连接时复位')
        self.jk_reset_check.setChecked(self.js_cfg.get('jk_con_reset', False))
        self.rtt_address_edit = QLineEdit(
            config_manager.format_rtt_search_text(self.js_cfg.get('rtt_block_address'))
        )
        self.rtt_address_edit.setPlaceholderText(
            '%s %s' % (
                config_manager.DEFAULT_RTT_SEARCH_START,
                config_manager.DEFAULT_RTT_SEARCH_SIZE,
            )
        )
        self.rtt_address_edit.setToolTip(
            'RTT 控制块搜索范围：起始地址 + 搜索长度，空格分隔。\n'
            '起始地址须 4 字节对齐，默认 %s %s。'
            % (
                config_manager.DEFAULT_RTT_SEARCH_START,
                config_manager.DEFAULT_RTT_SEARCH_SIZE,
            )
        )
        jk_form.addRow('芯片', self.chip_combo)
        jk_row = QHBoxLayout()
        jk_row.addWidget(QLabel('SN'))
        jk_row.addWidget(self.jk_sn_edit)
        jk_row.addWidget(QLabel('speed(kHz)'))
        jk_row.addWidget(self.jk_speed_edit)
        jk_row.addWidget(self.jk_reset_check)
        jk_form.addRow(jk_row)
        jk_form.addRow(
            '_SEGGER_RTT 地址搜索范围',
            self.rtt_address_edit,
        )
        connection_layout.addWidget(jk_box)

        ser_box = QGroupBox('串口参数')
        ser_form = QFormLayout(ser_box)
        self.com_combo = QComboBox()
        self.baud_combo = QComboBox()
        self._refresh_serial_lists()
        ser_form.addRow('串口', self.com_combo)
        ser_form.addRow('波特率', self.baud_combo)
        connection_layout.addWidget(ser_box)
        layout.addWidget(connection_group)

        display_group = QGroupBox('显示与编码')
        display_layout = QHBoxLayout(display_group)
        fmt_box = QGroupBox('字符编码格式')
        fmt_layout = QHBoxLayout(fmt_box)
        self.format_group = QButtonGroup(self)
        for key, label in [('utf-8', 'utf-8'), ('asc', 'asc'), ('hex', 'hex'), ('gb2312', 'gb2312')]:
            btn = QRadioButton(label)
            self.format_group.addButton(btn)
            fmt_layout.addWidget(btn)
            if self.js_cfg['char_format'] == key:
                btn.setChecked(True)
        display_layout.addWidget(fmt_box)

        lb_box = QGroupBox('发送 ASC 追加换行符')
        lb_layout = QHBoxLayout(lb_box)
        self.linebreak_group = QButtonGroup(self)
        for value, label in [('\r\n', r'\r\n'), ('\n', r'\n'), ('', 'none')]:
            btn = QRadioButton(label)
            self.linebreak_group.addButton(btn)
            lb_layout.addWidget(btn)
            if self.js_cfg['line_break'] == value:
                btn.setChecked(True)
        display_layout.addWidget(lb_box)

        theme_box = QGroupBox('界面主题')
        theme_layout = QHBoxLayout(theme_box)
        self.theme_combo = QComboBox()
        for theme_key in THEMES:
            self.theme_combo.addItem(THEME_LABELS[theme_key], theme_key)
        current_theme = normalize_theme(self.js_cfg.get('ui_theme', THEME_DARK))
        theme_index = self.theme_combo.findData(current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        display_layout.addWidget(theme_box)
        layout.addWidget(display_group)

        wave_group = QGroupBox('波形默认值')
        wave_form = QFormLayout(wave_group)
        self.y_min_edit = QLineEdit(str(self.js_cfg['y_range'][0]))
        self.y_max_edit = QLineEdit(str(self.js_cfg['y_range'][1]))
        self.y_label_edit = QLineEdit(self.js_cfg['y_label_text'])
        self.curves_edit = QLineEdit(self.js_cfg['curves_name'])
        wave_form.addRow('y轴下边界', self.y_min_edit)
        wave_form.addRow('y轴上边界', self.y_max_edit)
        wave_form.addRow('y轴名称', self.y_label_edit)
        wave_form.addRow('曲线名称', self.curves_edit)
        layout.addWidget(wave_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.jk_radio.toggled.connect(self._on_iface_changed)
        self.ser_radio.toggled.connect(self._on_iface_changed)

    def _populate_chip_combo(self):
        selected = self.js_cfg['jk_chip'][0] if self.js_cfg.get('jk_chip') else ''
        self.chip_combo.clear()
        catalog = get_chip_catalog(self.js_cfg)
        for vendor in iter_sorted_vendors(catalog):
            chips = catalog.get(vendor, [])
            if not chips:
                continue
            self.chip_combo.addItem(vendor)
            header_index = self.chip_combo.count() - 1
            header_item = self.chip_combo.model().item(header_index)
            if header_item is not None:
                header_item.setEnabled(False)
            for chip in chips:
                self.chip_combo.addItem(chip)
        if selected:
            index = self.chip_combo.findText(selected)
            if index >= 0:
                self.chip_combo.setCurrentIndex(index)
            else:
                vendor = detect_chip_vendor(selected)
                self.chip_combo.addItem(selected)
                self.js_cfg.setdefault('jk_chip_catalog', {}).setdefault(vendor, []).append(selected)
                self.chip_combo.setCurrentText(selected)
    def _refresh_serial_lists(self):
        self.com_des_list, self.com_name_list = bds_ser.serial_find()
        if not self.com_des_list:
            self.com_des_list.append('')
        _, resolved_des, self.com_des_list, self.com_name_list = bds_ser.resolve_serial_port(
            self.js_cfg.get('ser_com', ''), self.js_cfg.get('ser_des', '')
        )
        self.com_combo.clear()
        self.com_combo.addItems(self.com_des_list)
        if resolved_des in self.com_des_list:
            self.com_combo.setCurrentText(resolved_des)
        self.baud_combo.clear()
        self.baud_combo.addItems([str(v) for v in self.js_cfg['ser_baud']])
        self.baud_combo.setCurrentIndex(0)

    def _detect_serial_hotplug(self):
        default_des = bds_ser.ser_hot_plug_detect(
            self.com_combo.currentText(), self.com_des_list, self.com_name_list
        )
        if default_des:
            self.com_combo.setCurrentText(default_des)

    def _on_iface_changed(self):
        if self.jk_radio.isChecked():
            self.js_cfg['hw_sel'] = '1'
        else:
            self.js_cfg['hw_sel'] = '2'

    def _selected_format(self):
        for btn in self.format_group.buttons():
            if btn.isChecked():
                return btn.text()
        return self.js_cfg['char_format']

    def _selected_line_break(self):
        for btn in self.linebreak_group.buttons():
            if btn.isChecked():
                text = btn.text()
                if text == r'\r\n':
                    return '\r\n'
                if text == r'\n':
                    return '\n'
                return ''
        return self.js_cfg['line_break']

    def _save(self):
        try:
            address_text = self.rtt_address_edit.text().strip()
            if address_text:
                rtt_block_address = extract_and_convert_hex(address_text)
                if rtt_block_address is None:
                    QMessageBox.warning(
                        self,
                        '配置错误',
                        "请输入正确的起始搜索地址以及范围。十六进制字符串必须以 '0x' 或者 '0X' 开头，"
                        "两个值之间用空格隔开，起始地址必须 4 字节对齐。",
                    )
                    return
                self.js_cfg['rtt_block_address'] = list(rtt_block_address)
            else:
                self.js_cfg['rtt_block_address'] = list(config_manager.DEFAULT_RTT_BLOCK_ADDRESS)

            self.js_cfg['jk_speed'] = int(self.jk_speed_edit.text())
            self.js_cfg['y_range'][0] = int(self.y_min_edit.text())
            self.js_cfg['y_range'][1] = int(self.y_max_edit.text())
            self.js_cfg['y_label_text'] = self.y_label_edit.text()
            self.js_cfg['curves_name'] = self.curves_edit.text()

            baud = int(self.baud_combo.currentText())
            self.js_cfg['ser_baud'] = bds_ser.ser_buad_list_adjust(baud, self.js_cfg['ser_baud'])
            if len(self.js_cfg['ser_baud']) >= 10:
                self.js_cfg['ser_baud'].pop()
            self.js_cfg['ser_des'] = self.com_combo.currentText()
            try:
                self.js_cfg['ser_com'] = self.com_name_list[
                    self.com_des_list.index(self.com_combo.currentText())
                ]
            except Exception:
                self.js_cfg['ser_com'] = ''

            chip_name = self.chip_combo.currentText()
            if is_chip_header(chip_name):
                QMessageBox.warning(self, '配置错误', '请选择具体芯片型号，不能选择厂家分组标题。')
                return

            recent = [chip for chip in self.js_cfg.get('jk_chip', []) if chip and chip != chip_name]
            self.js_cfg['jk_chip'] = [chip_name] + recent[:9]
            vendor = detect_chip_vendor(chip_name)
            catalog = self.js_cfg.setdefault('jk_chip_catalog', {})
            vendor_chips = catalog.setdefault(vendor, [])
            if chip_name not in vendor_chips:
                vendor_chips.append(chip_name)
                vendor_chips.sort(key=str.casefold)
            self.js_cfg['jk_con_reset'] = self.jk_reset_check.isChecked()
            self.js_cfg['char_format'] = self._selected_format()
            self.js_cfg['line_break'] = self._selected_line_break()
            self.js_cfg['ui_theme'] = self.theme_combo.currentData() or THEME_DARK
            self.js_cfg['hw_sel'] = '1' if self.jk_radio.isChecked() else '2'
            config_manager.save_config(self.js_cfg)
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, '配置错误', str(exc))

    def closeEvent(self, event):
        self._hotplug_timer.stop()
        super().closeEvent(event)
