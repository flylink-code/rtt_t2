#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

export PYQTGRAPH_QT_LIB=PySide6

pip install -U pip
pip install -r requirements.txt pyinstaller

rm -rf build dist
pyinstaller rtt_t2.spec --noconfirm

VERSION="${RTT_VERSION:-v1.0.4}"
ARCHIVE="dist/rtt_t2-${VERSION}-linux-x64.tar.gz"
tar -czf "$ARCHIVE" -C dist rtt_t2
echo "Created $ARCHIVE"
