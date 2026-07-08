# RTT_T2 v1.0.2

English | [中文](README.md)

A Windows debugging tool (forked from [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2)) for **J-Link RTT** and **serial** logging, interactive terminals, payload sending, and live waveforms.

> Downloads: [GitHub Releases](https://github.com/flylink-code/rtt_t2/releases)

## v1.0.2

- **Windows MSI installer** on GitHub Releases with custom install directory
- **GitHub auto-update** on startup; Windows prefers MSI downloads
- **Per-user data** in `%LOCALAPPDATA%\rtt_t2\` for installed builds

## v1.0.1

- **J-Link RTT search**: default range `0x20000000 0x20000`, applied on connect from config
- **Config UX**: RTT fields show defaults and tooltips; empty values migrate automatically
- **Context-menu save**: pick save directory, remembers last path
- **Theme toggle**: quick dark / light switch in the toolbar

## What's New in v1.0.0

- **PySide6 UI**: sidebar + main workspace layout with dark / light themes
- **Dual view modes**: log mode (BDSCOL colors) and terminal mode (`pyte` VT100, MSH / ANSI)
- **Custom commands**: sidebar shortcuts for frequent payloads
- **Chip catalog**: vendor-grouped J-Link parts in config UI and `config.json`
- **Stability**: safe J-Link shutdown; waveform stack on PySide6 6.x / pyqtgraph 0.14

## User Interface

v1.0 is a full PySide6 rewrite. The window is organized as **toolbar**, **left sidebar**, **central display**, **send panel**, and **status bar**.

```text
┌──────────────────────────────────────────────────────────────┐
│ Toolbar: Connect | Config | Wave | Timestamp | Save | Find … │
├──────────┬───────────────────────────────────────────────────┤
│ Sidebar  │  [Optional] Filter dock: expression | enable | inv  │
│          ├───────────────────────────────────────────────────┤
│ HW mode  │                                                   │
│ View mode│              Main area (log / terminal)            │
│ Commands │                                                   │
│ Target   │                                                   │
│ Connect  │                                                   │
├──────────┴───────────────────────────────────────────────────┤
│ Send panel (log mode): ASC/HEX | history | encoding | EOL     │
├──────────────────────────────────────────────────────────────┤
│ Status: connection | target | RX | TX | view state           │
└──────────────────────────────────────────────────────────────┘
```

### Left sidebar

| Section | Description |
|---------|-------------|
| Interface | **J-Link RTT** / **Serial** (disconnect before switching) |
| View mode | **Log mode** / **Terminal mode** |
| Custom commands | Manage named ASC/HEX macros |
| Target | Active chip or COM port summary |
| Connect | Connect / disconnect |
| Config / Wave | Shortcuts |
| Log folder | Open `logs/` save directory |

### Main display

| Mode | Behavior |
|------|----------|
| **Log** | Read-only viewer with BDSCOL colors, filters, pause-follow, context menu |
| **Terminal** | Interactive `pyte` terminal with ANSI, history, Tab, Ctrl+C |

In **terminal mode** the bottom send panel is hidden; typing happens in the main area. In **log mode** the send panel is used for ASC / HEX payloads.

### Toolbar

Mirrors sidebar actions plus **timestamp**, **save all**, **real-time save**, **pause follow**, **scroll to bottom**, and **find** (`Ctrl+F`).

### Config dialog

- **Connection**: J-Link (vendor-grouped MCU, speed, reset, RTT search range) or serial (COM, baud)
- **Display & encoding**: utf-8 / asc / hex / gb2312, line ending, **UI theme**
- **Waveform defaults**: Y range, curve names, axis label

### Theme & fonts

- Theme: `ui_theme` → `dark` or `light` in `config.json`
- Default fonts: Cascadia Mono + Microsoft YaHei UI

## Features

| Feature | Details |
|---------|---------|
| J-Link RTT | utf-8 / asc; channel 0 only |
| Serial | utf-8 / asc / hex |
| Log mode | Colors, line filter, pause, Ctrl+F, save all |
| Terminal mode | MSH / shell, Enter / Tab / history / Ctrl+C |
| Waveform | Up to 3 curves, drag, stats, CSV export |
| Send panel | ASC / HEX, multiline, history, comments |

## Requirements

- **OS**: Windows 10+
- **Python**: 3.9+ (from source)
- **J-Link**: [SEGGER J-Link](https://www.segger.com/downloads/jlink/) for RTT (`JLink_x64.dll`)

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
```

Build (uses project `.venv`):

```bat
build.bat
```

Output: `dist\rtt_t2\` — run `rtt_t2.exe` inside that folder (keep the whole directory).

**Windows MSI** installers on GitHub Releases support a custom install directory. Config and logs live in `%LOCALAPPDATA%\rtt_t2\` so upgrades keep your settings.

## Auto-update

When `update_flag` is `true`, the app checks GitHub Releases on startup. On Windows it prefers the MSI asset and opens the installer after download.

## Project layout

```text
rtt_t2/
├─ app/                 PySide6 UI, themes, terminal widgets
│  ├─ dialogs/          config, find, update, custom commands
│  ├─ widgets/          log view, terminal view, send panel
│  ├─ services/         log processing, session helpers
│  └─ styles/           dark.qss / light.qss
├─ bds/                 J-Link, serial, waveform core
├─ docs/                developer docs
├─ scripts/             build & RTT diagnostics
├─ main.py              entry point
├─ config_manager.py    config & log directory
└─ rtt_t2.spec          PyInstaller spec
```

Docs:

- Chinese readme: [README.md](README.md)
- Source notes: [docs/source_code.md](docs/source_code.md)
- Structure: [docs/project_structure.md](docs/project_structure.md)

## Quick start

### J-Link RTT

1. **Config** → pick MCU (by vendor), speed, reset option → save → **Connect**
2. Switch **Log mode** or **Terminal mode** in the sidebar

> RTT channel 0 only (`SEGGER_RTT_printf(0, ...)`).

### Serial

**Config** → COM + baud → save → **Connect**

### Log filter (log mode only)

1. Filter dock: `TAG=DLOG` or `TAG=DLOG&&TAG=BDS`
2. Enable; use **Invert** to keep only matches
3. Prefer keywords with length ≥ 3

### Custom commands

Sidebar → add name, payload, ASC/HEX → send while connected.

### Waveform

**Config** → Y range and curve names (`X&&Y&&Z`) → connect → **Waveform**

Firmware format: `TAG=DLOG M*P(x,y,z)\n` (see below).

## Colored logs (BDSCOL)

```c
#define BDS_COLOR_TAG "BDSCOL"
#define BDS_LOG_COLOR_RED 0xFF3030

SEGGER_RTT_printf(0, BDS_COLOR_TAG "(%d)%s", BDS_LOG_COLOR_RED, "test\n");
```

## Waveform payload

```text
TAG=DLOG M*P(x,y,z)\n
```

- Integers: `P=0`
- Floats: scale by `10^P` (no `%f` in RTT printf)

One curve: `M*P(x,0,0)`; two curves: `M*P(x,y,0)`.

## Chip catalog

`jk_chip_catalog` in `config.json` lists parts by vendor; `jk_chip[0]` is the active MCU.

## FAQ

### `Expected to be given a valid DLL`

Install SEGGER J-Link or set `JLINK_SDK` to the DLL path.

### Target connects but no RTT output

Set RTT search range in **Config**, e.g. `0x20000000 0x20000`.

### Filter has no effect in terminal mode

Filtering applies to **log mode** only.

### Packaged app: `No module named 'pylink'`

Use `build.bat` or `scripts\package_windows.ps1` so the build runs inside `.venv` with all dependencies bundled.

---

## Credits

Free and open source. Upstream: [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2). Stars are appreciated.
