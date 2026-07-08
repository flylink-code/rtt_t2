# RTT_T2 v1.0.0

English | [中文](README.md)

A Windows debugging tool (forked from [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2)) for **J-Link RTT** and **serial** logging, interactive terminals, payload sending, and live waveforms.

> Downloads: [GitHub Releases](https://github.com/flylink-code/rtt_t2/releases)

## What's New in v1.0.0

- **PySide6 UI** with modular `app/` layout and dark / light themes
- **Dual view modes**: log mode (BDSCOL colors) and terminal mode (`pyte` VT100 shell with ANSI)
- **Custom commands** in the sidebar for one-click macros
- **Chip catalog** grouped by vendor in `config.json`
- **Stability**: safe J-Link teardown; waveform stack updated for PySide6 6.x and pyqtgraph 0.14

## Features

| Feature | Details |
|---------|---------|
| J-Link RTT | utf-8 / asc; often faster than RTT Viewer in practice |
| Serial | utf-8 / asc / hex |
| Log mode | Colored logs, line filter, pause-follow, Ctrl+F search, save all |
| Terminal mode | Interactive shell (MSH), Enter / Tab / history / Ctrl+C |
| Waveform | Up to 3 curves, drag, region stats, CSV export |
| Send panel | ASC / HEX, multiline, history, inline comments |

## Requirements

- **OS**: Windows 10+
- **Python**: 3.9+ (from source)
- **J-Link**: [SEGGER J-Link](https://www.segger.com/downloads/jlink/) when using RTT (`JLink_x64.dll`)

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
```

Build installer:

```bat
build.bat
```

## Layout

```text
rtt_t2/
├─ app/                 PySide6 UI, services, terminal widgets
├─ bds/                 J-Link, serial, waveform core
├─ docs/                Developer docs
├─ images/              Screenshots and demos
├─ scripts/             Build and RTT diagnostic scripts
├─ main.py              Entry point
├─ config_manager.py    Config and log directory helpers
└─ rtt_t2.spec          PyInstaller spec
```

Docs:

- Chinese readme: [README.md](README.md)
- Source notes: [docs/source_code.md](docs/source_code.md)
- Structure: [docs/project_structure.md](docs/project_structure.md)

## Quick Start

### J-Link RTT

1. Open **Config** → pick MCU (vendor groups), speed, reset option
2. Save → click **Connect**
3. Switch **Log mode** or **Terminal mode** in the sidebar

> Only RTT channel 0 is supported (`SEGGER_RTT_printf(0, ...)`).

### Serial

1. **Config** → COM port and baud rate
2. Save → **Connect**

### View Modes

| Mode | Use case |
|------|----------|
| Log | Colored tags, filters, boot logs |
| Terminal | RT-Thread MSH / interactive shell in the main pane |

In terminal mode the send panel is hidden; use **Custom commands** for shortcuts.

### Log Filter (log mode only)

1. Enter patterns like `TAG=DLOG` or `TAG=DLOG&&TAG=BDS`
2. Enable the filter; use **Invert** to keep only matching lines
3. Prefer keywords with length ≥ 3

### Waveform

1. Set Y range and curve names in **Config** (`X&&Y&&Z` for three curves)
2. Connect hardware → **Waveform**
3. Firmware sends `TAG=DLOG M*P(x,y,z)\n` (see below)

## Colored Logs (BDSCOL)

```c
#define BDS_COLOR_TAG "BDSCOL"
#define BDS_LOG_COLOR_RED 0xFF3030

SEGGER_RTT_printf(0, BDS_COLOR_TAG "(%d)%s", BDS_LOG_COLOR_RED, "test\n");
```

## Waveform Payload

```text
TAG=DLOG M*P(x,y,z)\n
```

- Integers: `P=0`
- Floats: scale by `10^P` because RTT printf has no `%f`

## Chip Catalog

`jk_chip_catalog` in `config.json` lists common parts by vendor; `jk_chip[0]` is the active selection. New names are auto-classified on save.

## FAQ

### `Expected to be given a valid DLL`

Install SEGGER J-Link or set `JLINK_SDK` to your DLL path.

### Target connects but no RTT output

Set RTT search range in **Config**, e.g. `0x20000000 0x20000` (4-byte aligned start, hex with `0x` prefix, values separated by space).

### Filter has no effect in terminal mode

Filtering applies to **log mode** only; terminal mode shows the raw stream.

---

## Credits

Free and open source. Upstream: [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2). Stars are appreciated.
