import logging as log
import sys

import requests
from PySide6.QtCore import QObject, QThread, Signal

from app.release_info import GITHUB_RELEASES_API, is_newer_version


def _fetch_latest_release():
    response = requests.get(
        GITHUB_RELEASES_API,
        timeout=10,
        headers={'Accept': 'application/vnd.github+json'},
    )
    response.raise_for_status()
    releases = response.json()
    for release in releases:
        if release.get('draft'):
            continue
        tag_name = release.get('tag_name', '')
        if tag_name:
            return release
    return None


def pick_release_asset(release):
    assets = release.get('assets', [])
    if not assets:
        return None
    if sys.platform.startswith('win'):
        platform_key = 'windows'
        extension = '.zip'
    else:
        platform_key = 'linux'
        extension = '.tar.gz'
    for asset in assets:
        name = asset.get('name', '').lower()
        if platform_key in name and name.endswith(extension):
            return asset
    return assets[0]


class UpdateCheckerWorker(QThread):
    update_available = Signal(dict)
    check_failed = Signal(str)

    def __init__(self, current_version, parent=None):
        super().__init__(parent)
        self._current_version = current_version

    def run(self):
        try:
            latest_release = _fetch_latest_release()
            if latest_release is None:
                return
            latest_tag = latest_release.get('tag_name', '')
            log.info('update check: current=%s latest=%s', self._current_version, latest_tag)
            if is_newer_version(latest_tag, self._current_version):
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
            asset = pick_release_asset(self._latest_release)
            if asset is None:
                raise RuntimeError('当前版本没有可下载的安装包，请到 GitHub Releases 页面手动下载')
            home_dir = os.path.expanduser('~')
            download_dir = os.path.join(home_dir, 'Downloads')
            os.makedirs(download_dir, exist_ok=True)
            download_url = asset['browser_download_url']
            filename = os.path.join(download_dir, asset['name'])
            response = requests.get(download_url, timeout=30, stream=True)
            response.raise_for_status()
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
