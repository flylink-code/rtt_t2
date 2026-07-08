import logging as log

import requests
from PySide6.QtCore import QObject, QThread, Signal


class UpdateCheckerWorker(QThread):
    update_available = Signal(dict)
    check_failed = Signal(str)

    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self._current_version = current_version

    def run(self):
        try:
            try:
                latest_release = requests.get(
                    "https://gitee.com/api/v5/repos/bds123/rtt_t2/releases",
                    timeout=5,
                ).json()[-1]
                log.info('download source: gitee')
            except Exception:
                latest_release = requests.get(
                    "https://api.github.com/repos/flylink-code/rtt_t2/releases",
                    timeout=5,
                ).json()[0]
                log.info('download source: github')

            if self._current_version != latest_release['tag_name']:
                self.update_available.emit(latest_release)
        except Exception as exc:
            self.check_failed.emit(str(exc))


class DownloadWorker(QThread):
    progress = Signal(int)
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, latest_release, parent=None):
        super().__init__(parent)
        self._latest_release = latest_release

    def run(self):
        import os

        try:
            home_dir = os.path.expanduser('~')
            download_dir = os.path.join(home_dir, 'Downloads')
            asset = self._latest_release['assets'][0]
            download_url = asset['browser_download_url']
            filename = os.path.join(download_dir, asset['name'])
            response = requests.get(download_url, timeout=5, stream=True)
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            last_percent = -1
            with open(filename, 'wb') as file_obj:
                for chunk in response.iter_content(1024):
                    if not chunk:
                        continue
                    file_obj.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = downloaded * 100 // total_size
                        if percent != last_percent:
                            self.progress.emit(percent)
                            last_percent = percent
            self.finished_ok.emit(filename)
        except Exception as exc:
            self.failed.emit(str(exc))


class HwBridge(QObject):
    error = Signal(str)
    warn = Signal(str)

    def on_error(self, message):
        self.error.emit(message)

    def on_warn(self, message):
        self.warn.emit(message)
