# RTT_T2 v1.0.6

English | [中文](README.md)

A Windows debugging tool (forked from [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2)) for **J-Link RTT** and **serial** logging, interactive terminals, payload sending, and live waveforms.

> Downloads: [GitHub Releases](https://github.com/flylink-code/rtt_t2/releases)

## v1.0.6

- **Automatic update**: after the installer download completes, the app notifies the user, closes automatically, and starts the installer

## v1.0.5

- **Default encoding**: new configurations now use `utf-8`
- **Status bar**: shows the active character encoding and updates immediately when changed

## v1.0.4

- **J-Link disconnect handling**: prevent duplicate error dialogs after an unexpected J-Link disconnect

## v1.0.3

- **UI cleanup**: connection/config/wave actions moved into menus; filter dialog; sidebar quick actions
- **About & update check**: Help menu with about info and manual GitHub update check
- **Status bar**: shows current filter state

## v1.0.2

- **Windows installers** on GitHub Releases: setup.exe (custom install dir) and zip
- **GitHub auto-update** on startup; Windows prefers installer downloads
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
│ Menu: Connection | View | Tools | Help           [Theme btn] │
├──────────┬───────────────────────────────────────────────────┤
│ Sidebar  │                                                   │
│ HW mode  │              Main area (log / terminal)            │
│ View mode│                                                   │
│ Commands │                                                   │
│ Target   │                                                   │
│ Connect  │                                                   │
├──────────┴───────────────────────────────────────────────────┤
│ Send panel (log mode): ASC/HEX | history | encoding | EOL     │
├──────────────────────────────────────────────────────────────┤
│ Status: connection | target | RX | TX | view | filter        │
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

### Menus

| Menu | Actions |
|------|---------|
| **Connection** | Connect/disconnect, hardware config, waveform, custom commands, log folder |
| **View** | Pause follow, scroll to bottom, timestamp, theme toggle |
| **Tools** | Find (`Ctrl+F`), filter settings, enable filter, save all, real-time save |
| **Help** | Check for updates, About |

Configure filter expressions under **Tools → Filter**; the status bar shows the current filter state.

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

**Windows installers** on GitHub Releases:
- `*-windows-x64-setup.exe` — wizard with **custom install directory** (recommended)
- `*-windows-x64.msi` — MSI package (when available)
- `*-windows-x64.zip` — portable build

Config and logs live in `%LOCALAPPDATA%\rtt_t2\`.

## Auto-update

When `update_flag` is `true`, the app queries **GitHub Releases** (`flylink-code/rtt_t2`) for a newer tag on startup. Windows prefers MSI, then setup.exe; the installer opens after download.

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

1. **Tools → Filter**: `TAG=DLOG` or `TAG=DLOG&&TAG=BDS`
2. Enable; use **Invert** to keep only matches
3. Quick toggle via **Tools → Enable filter**; prefer keywords with length ≥ 3

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
