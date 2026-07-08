import datetime
import logging as log
import os

import bds.bds_jlink as bds_jk
import bds.bds_serial as bds_ser
import bds.bds_waveform as wv
import config_manager
from PySide6.QtCore import QEvent, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.theme_loader import apply_theme
from app.dialogs.custom_commands_dialog import CustomCommandsDialog
from app.dialogs.find_dialog import FindDialog
from app.dialogs.hw_config_dialog import HwConfigDialog
from app.dialogs.update_dialog import UpdateDialog
from app.services.log_service import LogProcessor, db_data_check_error
from app.services.session_service import (
    connect_jlink,
    connect_serial,
    disconnect_hw,
    get_endpoint_display,
    get_hw_mode,
    get_line_break_display,
    get_line_break_value,
    get_target_display_name,
    is_terminal_layout,
    save_console_history,
    normalize_ui_layout,
    send_payload,
)
from app.themes import get_theme_colors, normalize_theme
from app.text_search import QtTextSearcher
from app.widgets.log_terminal import LogTerminalWidget
from app.widgets.pyte_terminal import PyteTerminalWidget
from app.widgets.send_panel import SendPanel
from app.workers.hw_reader_worker import HwReaderWorker, thread_lock
from app.workers.update_checker import DownloadWorker, HwBridge, UpdateCheckerWorker

RTT_VERSION = 'v1.0.0'


class ConnectionSidebar(QFrame):
    def __init__(self, js_cfg, parent=None):
        super().__init__(parent)
        self.setObjectName('connectionSidebar')
        self.setFixedWidth(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title = QLabel('RTT_T2')
        title.setObjectName('sidebarTitle')
        layout.addWidget(title)
        subtitle = QLabel('调试终端')
        subtitle.setObjectName('sidebarSubtitle')
        layout.addWidget(subtitle)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(line)

        layout.addWidget(QLabel('接口模式'))
        self.mode_group = QButtonGroup(self)
        self.jk_radio = QRadioButton('J-Link RTT')
        self.ser_radio = QRadioButton('串口')
        self.mode_group.addButton(self.jk_radio)
        self.mode_group.addButton(self.ser_radio)
        layout.addWidget(self.jk_radio)
        layout.addWidget(self.ser_radio)
        if get_hw_mode(js_cfg) == 'jlink':
            self.jk_radio.setChecked(True)
        else:
            self.ser_radio.setChecked(True)

        self.layout_options = QWidget()
        layout_options_layout = QVBoxLayout(self.layout_options)
        layout_options_layout.setContentsMargins(0, 0, 0, 0)
        layout_options_layout.setSpacing(6)
        layout_options_layout.addWidget(QLabel('视图模式'))
        self.layout_group = QButtonGroup(self)
        self.log_layout_radio = QRadioButton('日志模式')
        self.terminal_layout_radio = QRadioButton('终端模式')
        self.layout_group.addButton(self.log_layout_radio)
        self.layout_group.addButton(self.terminal_layout_radio)
        layout_options_layout.addWidget(self.log_layout_radio)
        layout_options_layout.addWidget(self.terminal_layout_radio)
        if normalize_ui_layout(js_cfg.get('ui_layout', 'log')) == 'terminal':
            self.terminal_layout_radio.setChecked(True)
        else:
            self.log_layout_radio.setChecked(True)
        layout.addWidget(self.layout_options)

        self.custom_cmds_btn = QPushButton('自定义命令')
        layout.addWidget(self.custom_cmds_btn)

        layout.addWidget(QLabel('目标'))
        self.target_label = QLabel(get_target_display_name(js_cfg))
        self.target_label.setWordWrap(True)
        layout.addWidget(self.target_label)
        self.endpoint_label = QLabel(get_endpoint_display(js_cfg))
        self.endpoint_label.setObjectName('sidebarSubtitle')
        layout.addWidget(self.endpoint_label)

        self.connect_btn = QPushButton('连接')
        self.connect_btn.setObjectName('primaryButton')
        layout.addWidget(self.connect_btn)

        row = QHBoxLayout()
        self.config_btn = QPushButton('配置')
        self.wave_btn = QPushButton('波形')
        row.addWidget(self.config_btn)
        row.addWidget(self.wave_btn)
        layout.addLayout(row)

        self.log_dir_btn = QPushButton('日志目录')
        layout.addWidget(self.log_dir_btn)
        layout.addStretch()

    def set_connected(self, connected):
        self.connect_btn.setText('断开连接' if connected else '连接')
        self.connect_btn.setProperty('connected', connected)
        self.connect_btn.style().unpolish(self.connect_btn)
        self.connect_btn.style().polish(self.connect_btn)

    def refresh_target(self, js_cfg):
        self.target_label.setText(get_target_display_name(js_cfg))
        self.endpoint_label.setText(get_endpoint_display(js_cfg))
        if get_hw_mode(js_cfg) == 'jlink':
            self.jk_radio.setChecked(True)
        else:
            self.ser_radio.setChecked(True)
        if normalize_ui_layout(js_cfg.get('ui_layout', 'log')) == 'terminal':
            self.terminal_layout_radio.setChecked(True)
        else:
            self.log_layout_radio.setChecked(True)

    def get_selected_layout(self):
        return 'terminal' if self.terminal_layout_radio.isChecked() else 'log'

    def get_selected_mode(self):
        return 'jlink' if self.jk_radio.isChecked() else 'serial'


class MainWindow(QMainWindow):
    def __init__(self, js_cfg):
        super().__init__()
        self.js_cfg = js_cfg
        self.connected = False
        self.rx_bytes = 0
        self.tx_bytes = 0
        self.real_time_save_file = ''
        self.real_time_save_enabled = False
        self.timestamp_enabled = False
        self.terminal_paused = js_cfg.get('terminal_paused', False)
        self.find_dialog = None
        self.update_dialog = None
        self.download_worker = None
        self.pending_update_file = ''
        self.log_processor = LogProcessor()

        self.hw_bridge = HwBridge()
        self.jk_obj = bds_jk.BDS_Jlink(self.hw_bridge.on_error, self.hw_bridge.on_warn, char_format=js_cfg['char_format'])
        self.ser_obj = bds_ser.BDS_Serial(self.hw_bridge.on_error, self.hw_bridge.on_warn, char_format=js_cfg['char_format'])
        self.hw_obj = self.ser_obj if get_hw_mode(js_cfg) == 'serial' else self.jk_obj

        self._build_ui()
        self._bind_shortcuts()
        self._connect_signals()

        wv.wave_init()
        self.jk_obj.reg_dlog_M_callback(wv.wave_data)
        self.ser_obj.reg_dlog_M_callback(wv.wave_data)

        self.reader_worker = HwReaderWorker(self.hw_obj, thread_lock, self)
        self.reader_worker.start()

        self.log_timer = QTimer(self)
        self.log_timer.setInterval(50)
        self.log_timer.timeout.connect(self._poll_logs)
        self.log_timer.start()

        if self.js_cfg.get('update_flag', True):
            self.update_worker = UpdateCheckerWorker(RTT_VERSION, self)
            self.update_worker.update_available.connect(self._on_update_available)
            self.update_worker.start()

        self._refresh_status()
        self.log_terminal.set_paused(self.terminal_paused)
        self.console_terminal.set_paused(self.terminal_paused)
        self._apply_ui_layout()

    def _active_terminal(self):
        if is_terminal_layout(self.js_cfg):
            return self.console_terminal
        return self.log_terminal

    def _apply_ui_layout(self):
        terminal_mode = is_terminal_layout(self.js_cfg)
        self.send_panel.setVisible(not terminal_mode)
        self.terminal_stack.setCurrentWidget(self.console_terminal if terminal_mode else self.log_terminal)
        self._sync_terminal_console_settings()
        self.text_searcher.set_text_widget(self._active_terminal())
        if terminal_mode:
            self.console_terminal.setFocus()
        self._refresh_status()

    def _sync_terminal_console_settings(self):
        self.console_terminal.set_line_break(self.js_cfg.get('line_break', '\n'))
        self.console_terminal.set_history_provider(lambda: self.js_cfg.get('user_input_data', []))

    def _build_ui(self):
        self.setWindowTitle(RTT_VERSION)
        self.setMinimumSize(1100, 700)
        icon_path = os.path.join(config_manager.get_app_dir(), 'tool.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        toolbar = QToolBar('主工具栏')
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.connect_action = QAction('连接', self)
        self.config_action = QAction('配置', self)
        self.wave_action = QAction('波形绘制', self)
        self.timestamp_action = QAction('时间戳', self)
        self.save_all_action = QAction('保存全部', self)
        self.realtime_save_action = QAction('实时保存', self)
        self.pause_action = QAction('暂停跟随', self)
        self.scroll_bottom_action = QAction('滚动到底', self)
        self.find_action = QAction('查找', self)
        for action in (
            self.connect_action, self.config_action, self.wave_action,
            self.timestamp_action, self.save_all_action, self.realtime_save_action,
            self.pause_action, self.scroll_bottom_action, self.find_action,
        ):
            toolbar.addAction(action)

        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.sidebar = ConnectionSidebar(self.js_cfg)
        root.addWidget(self.sidebar)

        right = QVBoxLayout()
        right.setSpacing(8)

        theme_colors = get_theme_colors(normalize_theme(self.js_cfg.get('ui_theme', 'dark')))
        self.log_terminal = LogTerminalWidget(
            self.js_cfg['font'][0],
            self.js_cfg['font_size'],
            default_text_color=theme_colors.terminal_fg,
            default_bg_color=theme_colors.terminal_bg,
            parent=self,
        )
        self.console_terminal = PyteTerminalWidget(
            self.js_cfg['font'][0],
            self.js_cfg['font_size'],
            default_text_color=theme_colors.terminal_fg,
            default_bg_color=theme_colors.terminal_bg,
            parent=self,
        )
        for terminal in (self.log_terminal, self.console_terminal):
            terminal.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            terminal.customContextMenuRequested.connect(self._terminal_context_menu)
        self.terminal_stack = QStackedWidget()
        self.terminal_stack.addWidget(self.log_terminal)
        self.terminal_stack.addWidget(self.console_terminal)
        self.text_searcher = QtTextSearcher(
            self.log_terminal, theme=normalize_theme(self.js_cfg.get('ui_theme', 'dark'))
        )
        right.addWidget(self.terminal_stack, stretch=1)

        self.send_panel = SendPanel(
            self.js_cfg, self.js_cfg['font'][0], self.js_cfg['font_size'], self
        )
        right.addWidget(self.send_panel)
        root.addLayout(right, stretch=1)
        self.setCentralWidget(central)

        self.filter_dock = QDockWidget('过滤器', self)
        self.filter_dock.setObjectName('filterDock')
        filter_widget = QWidget()
        filter_layout = QHBoxLayout(filter_widget)
        self.filter_edit = QLineEdit(self.js_cfg.get('filter', ''))
        self.filter_enable = QCheckBox('启用')
        self.filter_enable.setChecked(self.js_cfg.get('filter_en', False))
        self.filter_inverse = QCheckBox('取反')
        filter_layout.addWidget(QLabel('表达式'))
        filter_layout.addWidget(self.filter_edit, stretch=1)
        filter_layout.addWidget(self.filter_enable)
        filter_layout.addWidget(self.filter_inverse)
        self.filter_dock.setWidget(filter_widget)
        self.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea, self.filter_dock)
        self.filter_dock.setVisible(self.js_cfg.get('send_panel_mode', 'expanded') == 'expanded')

        status = QStatusBar()
        self.setStatusBar(status)
        self.status_connection = QLabel('未连接')
        self.status_target = QLabel(get_target_display_name(self.js_cfg))
        self.status_rx = QLabel('RX 0')
        self.status_tx = QLabel('TX 0')
        self.status_view = QLabel('跟随输出')
        for widget in (self.status_connection, self.status_target, self.status_rx, self.status_tx, self.status_view):
            status.addPermanentWidget(widget)

    def _bind_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+F'), self, activated=self._open_find_dialog)
        QShortcut(QKeySequence('Ctrl+Return'), self.send_panel.input_edit, activated=self._insert_send_newline)

    def _connect_signals(self):
        self.connect_action.triggered.connect(self._toggle_connection)
        self.sidebar.connect_btn.clicked.connect(self._toggle_connection)
        self.config_action.triggered.connect(self._open_config)
        self.sidebar.config_btn.clicked.connect(self._open_config)
        self.wave_action.triggered.connect(self._open_wave)
        self.sidebar.wave_btn.clicked.connect(self._open_wave)
        self.sidebar.log_dir_btn.clicked.connect(self._open_log_dir)
        self.timestamp_action.triggered.connect(self._toggle_timestamp)
        self.save_all_action.triggered.connect(self._save_all_data)
        self.realtime_save_action.triggered.connect(self._toggle_realtime_save)
        self.pause_action.triggered.connect(self._toggle_pause)
        self.scroll_bottom_action.triggered.connect(self._scroll_to_bottom)
        self.find_action.triggered.connect(self._open_find_dialog)
        self.send_panel.send_requested.connect(self._send_data)
        self.send_panel.history_delete_requested.connect(self._delete_history_item)

        self.sidebar.jk_radio.toggled.connect(self._on_mode_radio_changed)
        self.sidebar.ser_radio.toggled.connect(self._on_mode_radio_changed)
        self.sidebar.log_layout_radio.toggled.connect(self._on_layout_changed)
        self.sidebar.terminal_layout_radio.toggled.connect(self._on_layout_changed)
        self.sidebar.custom_cmds_btn.clicked.connect(self._open_custom_commands)

        self.console_terminal.line_committed.connect(self._on_console_line_committed)
        self.console_terminal.bytes_send_requested.connect(self._on_console_bytes_send)
        self._sync_terminal_console_settings()

        self.filter_edit.textChanged.connect(self._save_filter_config)
        self.filter_enable.toggled.connect(self._save_filter_config)
        self.send_panel.char_format_combo.currentTextChanged.connect(self._on_char_format_changed)
        self.send_panel.line_break_combo.currentTextChanged.connect(self._on_line_break_changed)

        self.hw_bridge.error.connect(self._on_hw_error)
        self.hw_bridge.warn.connect(self._on_hw_warn)

        self.send_panel.input_edit.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj is self.send_panel.input_edit and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    self._insert_send_newline()
                    return True
                self._send_data()
                return True
            if event.key() == Qt.Key.Key_Up:
                self.send_panel.cycle_history('up')
                return True
            if event.key() == Qt.Key.Key_Down:
                self.send_panel.cycle_history('down')
                return True
        return super().eventFilter(obj, event)

    def _insert_send_newline(self):
        cursor = self.send_panel.input_edit.textCursor()
        cursor.insertText('\n')
        self.send_panel.input_edit.setTextCursor(cursor)

    def _on_mode_radio_changed(self):
        if self.connected:
            self.sidebar.refresh_target(self.js_cfg)
            QMessageBox.information(self, '提示', '请先断开当前连接后再切换接口模式')
            return
        self.js_cfg['hw_sel'] = '1' if self.sidebar.get_selected_mode() == 'jlink' else '2'
        self.hw_obj = self.jk_obj if self.js_cfg['hw_sel'] == '1' else self.ser_obj
        self.reader_worker.set_hw_obj(self.hw_obj)
        config_manager.save_config(self.js_cfg)
        self.sidebar.refresh_target(self.js_cfg)
        self._apply_ui_layout()
        self._refresh_status()

    def _on_layout_changed(self):
        self.js_cfg['ui_layout'] = self.sidebar.get_selected_layout()
        config_manager.save_config(self.js_cfg)
        self._apply_ui_layout()

    def _toggle_connection(self):
        wv.wave_cmd('wave reset')
        mode = get_hw_mode(self.js_cfg)
        if self.connected:
            for line in disconnect_hw(self.hw_obj, mode):
                self._active_terminal().append_plain(line)
            self.connected = False
            self.timestamp_enabled = False
            self.timestamp_action.setText('时间戳')
        else:
            try:
                thread_lock.acquire()
                self.hw_obj = self.jk_obj if mode == 'jlink' else self.ser_obj
                self.reader_worker.set_hw_obj(self.hw_obj)
                thread_lock.release()
                if mode == 'jlink':
                    ok, lines = connect_jlink(self.hw_obj, self.js_cfg)
                else:
                    ok, lines = connect_serial(self.hw_obj, self.js_cfg)
                for line in lines:
                    self._active_terminal().append_plain(line)
                self.connected = ok
            except Exception as exc:
                self.hw_obj.hw_close()
                log.info('connect failed: %s', exc)
                self._active_terminal().append_plain('[LOG] Error:%s\n' % exc)
                self.connected = False
        self._refresh_status()

    def _open_config(self):
        if self.connected:
            QMessageBox.information(self, '提示', '请先断开硬件连接！')
            return
        dialog = HwConfigDialog(self.js_cfg, self)
        if dialog.exec():
            self.hw_obj = self.jk_obj if self.js_cfg['hw_sel'] == '1' else self.ser_obj
            self.reader_worker.set_hw_obj(self.hw_obj)
            self.jk_obj.hw_set_char_format(self.js_cfg['char_format'])
            self.ser_obj.hw_set_char_format(self.js_cfg['char_format'])
            self.send_panel.char_format_combo.setCurrentText(self.js_cfg['char_format'])
            self.send_panel.line_break_combo.setCurrentText(get_line_break_display(self.js_cfg['line_break']))
            self.sidebar.refresh_target(self.js_cfg)
            self._refresh_status()
            self._apply_theme()
            self._apply_ui_layout()

    def _apply_theme(self):
        app = QApplication.instance()
        if app is None:
            return
        theme = apply_theme(app, self.js_cfg)
        colors = get_theme_colors(theme)
        self.log_terminal.apply_theme_colors(colors.terminal_fg, colors.terminal_bg)
        self.console_terminal.apply_theme_colors(colors.terminal_fg, colors.terminal_bg)
        self.text_searcher.set_theme(theme)

    def _open_wave(self):
        if not self.hw_obj.hw_is_open():
            QMessageBox.information(self, '提示', '请先连接硬件')
            return
        if not self.js_cfg['curves_name'].strip():
            QMessageBox.information(self, '提示', '没有设置任何轴名称，请至少设置一个轴名称')
            return
        wv.wave_cmd('wave reset')
        wv.startup_wave(
            self.js_cfg['y_range'],
            self.js_cfg['y_label_text'],
            [v for v in self.js_cfg['curves_name'].split('&&') if v],
        )

    def _open_log_dir(self):
        try:
            os.startfile(config_manager.ensure_log_dir())
        except Exception as exc:
            QMessageBox.warning(self, '错误', str(exc))

    def _toggle_timestamp(self):
        if not self.connected:
            QMessageBox.information(self, '提示', '请先连接硬件')
            return
        if not self.timestamp_enabled:
            self.hw_obj.open_timestamp()
            self.timestamp_enabled = True
            self.timestamp_action.setText('关闭时间戳')
        else:
            self.hw_obj.close_timestamp()
            self.timestamp_enabled = False
            self.timestamp_action.setText('时间戳')

    def _toggle_realtime_save(self):
        if not self.real_time_save_enabled:
            file_name = self._save_data_to_file('', prefix='real_time_log')
            if file_name:
                self.real_time_save_file = file_name
                self.real_time_save_enabled = True
                self.realtime_save_action.setText('停止实时保存')
        else:
            self.real_time_save_enabled = False
            self.realtime_save_file = ''
            self.realtime_save_action.setText('实时保存')

    def _save_all_data(self):
        data = self._active_terminal().get_all_text()
        if not data:
            QMessageBox.warning(self, '错误', '无数据!!!')
            return
        file_name = self._save_data_to_file(data)
        if file_name:
            os.startfile(file_name)

    def _save_data_to_file(self, data, prefix='log'):
        try:
            log_dir = config_manager.ensure_log_dir()
            file_name = os.path.join(
                log_dir,
                '%s_%s.txt' % (prefix, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')),
            )
            with open(file_name, 'w', encoding='utf-8') as file_obj:
                file_obj.write(data)
            return file_name
        except Exception as exc:
            QMessageBox.warning(self, '错误', str(exc))
            return None

    def _toggle_pause(self):
        self.terminal_paused = not self.terminal_paused
        self.js_cfg['terminal_paused'] = self.terminal_paused
        self.log_terminal.set_paused(self.terminal_paused)
        self.console_terminal.set_paused(self.terminal_paused)
        self.pause_action.setText('恢复跟随' if self.terminal_paused else '暂停跟随')
        config_manager.save_config(self.js_cfg)
        self._refresh_status()

    def _scroll_to_bottom(self):
        self.terminal_paused = False
        self.log_terminal.set_paused(False)
        self.console_terminal.set_paused(False)
        self.log_terminal.scroll_to_bottom()
        self.console_terminal.scroll_to_bottom()
        self._refresh_status()

    def _terminal_context_menu(self, pos):
        terminal = self.sender()
        if terminal is None:
            terminal = self._active_terminal()
        menu = QMenu(self)
        if terminal.textCursor().hasSelection():
            copy_action = menu.addAction('复制')
            copy_action.triggered.connect(terminal.copy)
        clear_action = menu.addAction('清除窗口数据')
        scroll_action = menu.addAction('滚动到最底端')
        action = menu.exec(terminal.mapToGlobal(pos))
        if action == clear_action:
            terminal.clear_terminal()
            self.rx_bytes = 0
            self._refresh_status()
        elif action == scroll_action:
            self._scroll_to_bottom()

    def _open_find_dialog(self):
        if self.find_dialog is None:
            self.find_dialog = FindDialog(self.js_cfg.get('search_history', []), self)
            self.find_dialog.find_requested.connect(self._on_find_requested)
            self.find_dialog.finished.connect(self._on_find_closed)
            self.text_searcher.reset()
        self.find_dialog.show()
        self.find_dialog.raise_()
        self.find_dialog.activateWindow()

    def _on_find_closed(self):
        self.text_searcher.reset()
        self.find_dialog = None

    def _on_find_requested(self, keyword, direction):
        if not keyword:
            QMessageBox.information(self, '查找', '请输入需要查找字符串')
            return
        history = self.js_cfg.setdefault('search_history', [])
        if keyword not in history:
            history.insert(0, keyword)
            self.js_cfg['search_history'] = history[:10]
            config_manager.save_config(self.js_cfg)
            if self.find_dialog:
                self.find_dialog.add_history_item(keyword)
        self.text_searcher.search(keyword, direction)

    def _send_data(self):
        sent, message, ok = send_payload(
            self.hw_obj,
            self.js_cfg,
            self.send_panel.get_input_text(),
            self.send_panel.get_tx_type(),
        )
        if not ok:
            if message == '请先连接硬件！':
                QMessageBox.warning(self, '提示', message)
                self._active_terminal().append_plain('[RTT_LOG]请先连接硬件！\n')
            elif message:
                QMessageBox.warning(self, '发送错误', message)
            return
        self.send_panel.set_history(self.js_cfg['user_input_data'])
        self.tx_bytes += sent
        self._refresh_status()

    def _on_console_bytes_send(self, byte_list):
        if not is_terminal_layout(self.js_cfg) or not self.hw_obj.hw_is_open():
            return
        payload = list(byte_list)
        if not payload:
            return
        self.hw_obj.hw_write(payload)
        self.tx_bytes += len(payload)
        self._refresh_status()

    def _on_console_line_committed(self, line):
        if not is_terminal_layout(self.js_cfg):
            return
        save_console_history(self.js_cfg, line)

    def _open_custom_commands(self):
        dialog = CustomCommandsDialog(self.js_cfg, self.hw_obj, self)
        dialog.command_send_requested.connect(self._on_custom_command_sent)
        dialog.exec()

    def _on_custom_command_sent(self, command):
        self._active_terminal().append_plain('[CMD] %s\n' % command.get('name', ''))
        content = command.get('content', '')
        tx_type = command.get('tx_type', 'ASC')
        if tx_type == 'HEX':
            sent = len([part for part in content.split() if part.strip()])
        else:
            sent = len((content + self.js_cfg.get('line_break', '\n')).encode('utf-8', errors='ignore'))
        self.tx_bytes += sent
        self._refresh_status()

    def _delete_history_item(self):
        current = self.send_panel.history_combo.currentText()
        if current in self.js_cfg['user_input_data']:
            self.js_cfg['user_input_data'].remove(current)
            config_manager.save_config(self.js_cfg)
            self.send_panel.set_history(self.js_cfg['user_input_data'])

    def _save_filter_config(self):
        self.js_cfg['filter'] = self.filter_edit.text()
        self.js_cfg['filter_en'] = self.filter_enable.isChecked()
        config_manager.save_config(self.js_cfg)

    def _on_char_format_changed(self, value):
        self.js_cfg['char_format'] = value
        self.jk_obj.hw_set_char_format(value)
        self.ser_obj.hw_set_char_format(value)
        config_manager.save_config(self.js_cfg)
        self._refresh_status()

    def _on_line_break_changed(self, value):
        self.js_cfg['line_break'] = get_line_break_value(value)
        config_manager.save_config(self.js_cfg)
        self.console_terminal.set_line_break(self.js_cfg['line_break'])

    def _poll_logs(self):
        if is_terminal_layout(self.js_cfg):
            result = self._poll_terminal_rx()
        else:
            result = self.log_processor.process_queue(
                self.hw_obj,
                self.js_cfg,
                self.filter_enable.isChecked(),
                self.filter_edit.text(),
                self.filter_inverse.isChecked(),
            )
            if result:
                self.log_terminal.append_log_result(result)
        if result:
            if self.real_time_save_enabled and result.get('save_text'):
                try:
                    with open(self.real_time_save_file, 'a', encoding='utf-8') as file_obj:
                        file_obj.write(result['save_text'])
                except Exception as exc:
                    log.info('realtime save error: %s', exc)
            if result.get('size', 0) > 0:
                self.rx_bytes += result['size']
                self._refresh_status()

    def _poll_terminal_rx(self):
        raw_log = []
        self.hw_obj.read_data_queue(raw_log)
        if not raw_log:
            return None

        text = ''.join(raw_log)
        if self.js_cfg['char_format'] == 'hex':
            self.console_terminal.feed_text(text)
            return {'save_text': text, 'size': len(text)}

        if db_data_check_error(text):
            error_text = "RTT数据出错，可能需要重启设备！ + error data:[" + text[0:20] + "]\n"
            self.console_terminal.feed_text(error_text)
            return {'save_text': '', 'size': 0}

        self.console_terminal.feed_text(text)
        return {'save_text': text, 'size': len(text)}

    def _on_hw_error(self, message):
        self.hw_obj.hw_close()
        self.connected = False
        prefix = '[Serial LOG]串口错误:' if get_hw_mode(self.js_cfg) == 'serial' else '[J_Link LOG]J_Link错误:'
        self._active_terminal().append_plain(prefix + message + '\n')
        QMessageBox.warning(self, '硬件错误', message)
        self._refresh_status()

    def _on_hw_warn(self, message):
        self._active_terminal().append_plain('[BDS LOG] ' + message)

    def _on_update_available(self, latest_release):
        if self.update_dialog is not None:
            return
        self.update_dialog = UpdateDialog(latest_release, self)
        self.update_dialog.download_requested.connect(
            lambda: self._start_download(latest_release)
        )
        result = self.update_dialog.exec()
        if result and self.update_dialog.get_download_path():
            self.pending_update_file = self.update_dialog.get_download_path()
        self.update_dialog = None

    def _start_download(self, latest_release):
        if self.download_worker is not None:
            return
        if self.update_dialog:
            self.update_dialog.mark_downloading()
        self.download_worker = DownloadWorker(latest_release, self)
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.finished_ok.connect(self._on_download_finished)
        self.download_worker.failed.connect(self._on_download_failed)
        self.download_worker.finished.connect(self._clear_download_worker)
        self.download_worker.start()

    def _on_download_progress(self, percent):
        if self.update_dialog:
            self.update_dialog.set_progress(percent)

    def _on_download_finished(self, path):
        if self.update_dialog:
            self.update_dialog.set_download_path(path)
            self.update_dialog.set_progress(100)
            self.update_dialog.accept()

    def _on_download_failed(self, message):
        if self.update_dialog:
            self.update_dialog.show_error(message)

    def _clear_download_worker(self):
        self.download_worker = None

    def _refresh_status(self):
        self.connected = self.hw_obj.hw_is_open()
        self.sidebar.set_connected(self.connected)
        self.connect_action.setText('断开连接' if self.connected else '连接')
        self.status_connection.setText('已连接' if self.connected else '未连接')
        self.status_target.setText(get_target_display_name(self.js_cfg))
        self.status_rx.setText('RX %d' % self.rx_bytes)
        self.status_tx.setText('TX %d' % self.tx_bytes)
        if self.terminal_paused:
            view = '暂停'
        elif is_terminal_layout(self.js_cfg):
            view = '终端模式'
        elif self._active_terminal().should_auto_scroll():
            view = '跟随输出'
        else:
            view = '浏览历史'
        self.status_view.setText(view)

    def closeEvent(self, event):
        self.js_cfg['terminal_paused'] = self.terminal_paused
        self.js_cfg['terminal_autoscroll'] = self._active_terminal().should_auto_scroll()
        config_manager.save_config(self.js_cfg)
        self.log_timer.stop()
        self.reader_worker.stop()
        thread_lock.acquire()
        try:
            self.jk_obj.hw_close()
            self.ser_obj.hw_close()
        finally:
            thread_lock.release()
        if self.pending_update_file:
            os.startfile(self.pending_update_file)
        event.accept()
