from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.release_info import (
    APP_DESCRIPTION,
    APP_DISPLAY_NAME,
    GITHUB_RELEASES_PAGE,
    GITHUB_REPO_PAGE,
    UPSTREAM_REPO_PAGE,
)


class AboutDialog(QDialog):
    def __init__(self, version, icon_path='', parent=None):
        super().__init__(parent)
        self.setWindowTitle('关于 %s' % APP_DISPLAY_NAME)
        self.setMinimumWidth(480)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = QHBoxLayout()
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(64, 64))
            header.addWidget(icon_label)

        title_box = QVBoxLayout()
        title = QLabel('<b style="font-size:18px;">%s</b>' % APP_DISPLAY_NAME)
        version_label = QLabel('当前版本：%s' % version)
        title_box.addWidget(title)
        title_box.addWidget(version_label)
        header.addLayout(title_box, stretch=1)
        layout.addLayout(header)

        desc = QLabel(APP_DESCRIPTION)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        features = QLabel(
            '主要功能：\n'
            '• J-Link RTT / 串口日志查看与发送\n'
            '• 日志模式（BDSCOL 彩色）与终端模式（VT100）\n'
            '• 自定义命令、日志过滤、波形观察\n'
            '• GitHub Releases 自动检测更新'
        )
        features.setWordWrap(True)
        layout.addWidget(features)

        links = QLabel(
            '项目主页：<a href="%s">%s</a><br>'
            '发行版下载：<a href="%s">%s</a><br>'
            '上游项目：<a href="%s">%s</a>'
            % (
                GITHUB_REPO_PAGE,
                GITHUB_REPO_PAGE,
                GITHUB_RELEASES_PAGE,
                GITHUB_RELEASES_PAGE,
                UPSTREAM_REPO_PAGE,
                UPSTREAM_REPO_PAGE,
            )
        )
        links.setOpenExternalLinks(True)
        links.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(links)

        self.status_label = QLabel('')
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.check_btn = QPushButton('检查更新')
        btn_row.addWidget(self.check_btn)
        btn_row.addStretch()
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        btn_row.addWidget(buttons)
        layout.addLayout(btn_row)

    def set_checking(self, checking):
        self.check_btn.setEnabled(not checking)
        if checking:
            self.status_label.setText('正在检查 GitHub 最新版本…')

    def set_status(self, message):
        self.status_label.setText(message)
        self.check_btn.setEnabled(True)
