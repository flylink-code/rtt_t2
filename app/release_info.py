GITHUB_REPO = 'flylink-code/rtt_t2'
GITHUB_REPO_PAGE = 'https://github.com/%s' % GITHUB_REPO
GITHUB_RELEASES_API = 'https://api.github.com/repos/%s/releases' % GITHUB_REPO
GITHUB_LATEST_RELEASE_API = 'https://api.github.com/repos/%s/releases/latest' % GITHUB_REPO
GITHUB_RELEASES_PAGE = 'https://github.com/%s/releases' % GITHUB_REPO
GITHUB_API_HEADERS = {
    'Accept': 'application/vnd.github+json',
    'User-Agent': 'rtt_t2-updater',
}
GITEE_REPO = 'zworkspace/rtt_t2'
GITEE_REPO_PAGE = 'https://gitee.com/%s' % GITEE_REPO
GITEE_RELEASES_API = 'https://gitee.com/api/v5/repos/%s/releases' % GITEE_REPO
GITEE_RELEASES_PAGE = GITEE_REPO_PAGE + '/releases'
GITEE_API_HEADERS = {
    'Accept': 'application/json',
    'User-Agent': 'rtt_t2-updater',
}
UPSTREAM_REPO_PAGE = 'https://github.com/lh-hg/rtt_t2'
LOG_DIR_NAME = 'logs'
APP_DATA_DIR_NAME = 'rtt_t2'
APP_DISPLAY_NAME = 'RTT_T2'
APP_DESCRIPTION = (
    '基于 J-Link RTT 与串口的嵌入式调试工具，支持彩色日志、交互终端、'
    '自定义命令发送与波形观察。'
)


def normalize_version_tag(tag):
    if not tag:
        return ''
    return str(tag).lstrip('vV').strip()


def version_tuple(tag):
    normalized = normalize_version_tag(tag)
    parts = []
    for part in normalized.split('.'):
        number = part.split('-', 1)[0]
        try:
            parts.append(int(number))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer_version(latest_tag, current_tag):
    return version_tuple(latest_tag) > version_tuple(current_tag)
