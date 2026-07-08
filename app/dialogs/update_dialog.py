from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from app.release_info import GITHUB_RELEASES_PAGE


class UpdateDialog(QDialog):
    download_requested = Signal()

    def __init__(self, latest_release, parent=None):
        super().__init__(parent)
        self._latest_release = latest_release
        self._download_path = ''
        self.setWindowTitle('更新提醒')
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        ver_info = '软件更新: ' + latest_release['tag_name'] + '\n' + latest_release.get('body', '')
        self.info_label = QLabel(ver_info.replace('\r\n', '\n'))
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        github = QLabel('<a href="%s">GitHub 下载地址</a>' % GITHUB_RELEASES_PAGE)
        github.setOpenExternalLinks(True)
        layout.addWidget(github)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        self.status_label = QLabel('0%')
        layout.addWidget(self.status_label)

        btn_row = QVBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.download_btn = QPushButton('立刻更新')
        self.download_btn.clicked.connect(self._on_download_clicked)
        btn_row.addWidget(self.download_btn)
        self.later_btn = QPushButton('下次更新')
        self.later_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.later_btn)
        layout.addLayout(btn_row)

        self._downloading = False

    def _on_download_clicked(self):
        if self._downloading:
            return
        self.download_requested.emit()

    def mark_downloading(self):
        self._downloading = True
        self.download_btn.setText('下载中...')
        self.download_btn.setEnabled(False)

    def set_progress(self, percent):
        self.progress.setValue(percent)
        self.status_label.setText('%d%%' % percent)

    def set_download_path(self, path):
        self._download_path = path

    def get_download_path(self):
        return self._download_path

    def show_error(self, message):
        self.status_label.setText('下载异常: ' + message)
        self.download_btn.setText('立刻更新')
        self.download_btn.setEnabled(True)
        self._downloading = False
