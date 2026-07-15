import logging as log
import sys

import requests
from PySide6.QtCore import QObject, QThread, Signal

from app.release_info import (
    GITEE_API_HEADERS,
    GITEE_RELEASES_API,
    GITEE_RELEASES_PAGE,
    GITHUB_API_HEADERS,
    GITHUB_LATEST_RELEASE_API,
    GITHUB_RELEASES_API,
    GITHUB_RELEASES_PAGE,
    is_newer_version,
)


def _is_in_china():
    response = requests.get('https://www.cloudflare.com/cdn-cgi/trace', timeout=3)
    response.raise_for_status()
    return 'loc=CN' in response.text


def _get_release_sources():
    github = ('GitHub', GITHUB_RELEASES_API, GITHUB_API_HEADERS, GITHUB_RELEASES_PAGE)
    gitee = ('Gitee', GITEE_RELEASES_API, GITEE_API_HEADERS, GITEE_RELEASES_PAGE)
    try:
        return (gitee, github) if _is_in_china() else (github, gitee)
    except Exception as exc:
        log.info('update region lookup failed, using Gitee first: %s', exc)
        return gitee, github


def _fetch_github_release():
    try:
        response = requests.get(
            GITHUB_LATEST_RELEASE_API,
            timeout=10,
            headers=GITHUB_API_HEADERS,
        )
        if response.status_code == 404:
            raise RuntimeError('no latest release')
        response.raise_for_status()
        release = response.json()
        if release.get('draft'):
            raise RuntimeError('latest release is draft')
        return release
    except Exception as exc:
        log.info('GitHub latest release lookup failed, falling back to release list: %s', exc)
    return None


def _fetch_latest_release_from(source):
    name, releases_api, headers, releases_page = source
    if name == 'GitHub':
        release = _fetch_github_release()
        if release is not None:
            release['release_page'] = releases_page
            return release

    response = requests.get(releases_api, timeout=10, headers=headers)
    response.raise_for_status()
    for release in response.json():
        if release.get('draft') or release.get('prerelease'):
            continue
        if release.get('tag_name'):
            release['release_page'] = releases_page
            return release
    return None


def _fetch_latest_release():
    releases = []
    errors = []
    for source in _get_release_sources():
        try:
            release = _fetch_latest_release_from(source)
            if release is not None:
                releases.append((source[0], release))
        except Exception as exc:
            errors.append('%s: %s' % (source[0], exc))
            log.info('update lookup failed for %s: %s', source[0], exc)
    if releases:
        source_name, release = releases[0]
        for candidate_source, candidate_release in releases[1:]:
            if is_newer_version(candidate_release.get('tag_name', ''), release.get('tag_name', '')):
                source_name, release = candidate_source, candidate_release
        log.info('using %s update source', source_name)
        return release
    if errors:
        raise RuntimeError('; '.join(errors))
    return None


def pick_release_asset(release):
    assets = release.get('assets', [])
    if not assets:
        return None

    if sys.platform.startswith('win'):
        candidates = [
            asset for asset in assets
            if 'windows' in asset.get('name', '').lower()
        ]
        for asset in candidates:
            name = asset.get('name', '').lower()
            if name.endswith('.msi'):
                return asset
        for asset in candidates:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and 'setup' in name:
                return asset
        for asset in candidates:
            name = asset.get('name', '').lower()
            if name.endswith('.zip'):
                return asset
        return candidates[0] if candidates else assets[0]

    for asset in assets:
        name = asset.get('name', '').lower()
        if 'linux' in name and name.endswith('.tar.gz'):
            return asset
    return assets[0]


class UpdateCheckerWorker(QThread):
    update_available = Signal(dict)
    already_latest = Signal(str)
    check_failed = Signal(str)

    def __init__(self, current_version, parent=None, notify_when_latest=False):
        super().__init__(parent)
        self._current_version = current_version
        self._notify_when_latest = notify_when_latest

    def run(self):
        try:
            latest_release = _fetch_latest_release()
            if latest_release is None:
                if self._notify_when_latest:
                    self.check_failed.emit('未找到可用的 GitHub Release')
                return
            latest_tag = latest_release.get('tag_name', '')
            log.info('update check: current=%s latest=%s', self._current_version, latest_tag)
            if is_newer_version(latest_tag, self._current_version):
                self.update_available.emit(latest_release)
            elif self._notify_when_latest:
                self.already_latest.emit(latest_tag or self._current_version)
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
                raise RuntimeError('当前版本没有可下载的安装包，请到发行版页面手动下载')
            home_dir = os.path.expanduser('~')
            download_dir = os.path.join(home_dir, 'Downloads')
            os.makedirs(download_dir, exist_ok=True)
            download_url = asset.get('browser_download_url') or asset.get('download_url')
            if not download_url:
                raise RuntimeError('当前版本的安装包没有下载地址')
            filename = os.path.join(download_dir, asset['name'])
            response = requests.get(
                download_url,
                timeout=60,
                stream=True,
                headers=GITHUB_API_HEADERS,
            )
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
