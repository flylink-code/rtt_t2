# RTT_T2 v1.0.5

[English](README_EN.md) | 中文

基于 [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2) fork 的 Windows 嵌入式调试工具，面向 **J-Link RTT** 与 **串口** 日志查看、交互终端、数据发送和波形观察。

> 发行版与更新见 [GitHub Releases](https://github.com/flylink-code/rtt_t2/releases)

## v1.0.5 更新

- **默认编码**：新配置默认使用 `utf-8`
- **状态栏**：显示当前字符编码，切换编码后即时更新

## v1.0.4 更新

- **J-Link 断连处理**：修复 J-Link 意外断开后重复弹出异常提示的问题

## v1.0.3 更新

- **界面优化**：连接/配置/波形等收进菜单；过滤器改为对话框；侧栏增加快捷操作
- **关于与版本检查**：帮助菜单提供关于说明，支持手动检查 GitHub 更新
- **状态栏**：显示当前过滤状态

## v1.0.2 更新

- **Windows 安装包**：GitHub Releases 提供 setup.exe（可选安装目录）与 zip
- **GitHub 自动更新**：启动时检测 GitHub 最新版，Windows 优先下载安装包
- **安装版数据目录**：配置与日志保存在 `%LOCALAPPDATA%\rtt_t2\`

## v1.0.1 更新

- **J-Link RTT 搜索**：默认搜索范围 `0x20000000 0x20000`，连接时自动应用配置
- **配置优化**：RTT 地址在配置界面默认显示与提示；空配置自动迁移
- **右键保存日志**：可选保存目录，记住上次路径
- **主题切换**：工具栏右上角一键切换深色 / 亮色

## v1.0.0 亮点

- **PySide6 现代化界面**：侧边栏 + 主工作区布局，深色 / 浅色主题可切换
- **双视图模式**：日志模式（BDSCOL 彩色解析）与终端模式（`pyte` VT100，支持 MSH / ANSI）
- **自定义命令**：侧边栏配置常用指令，一键发送
- **芯片目录**：配置对话框与 `config.json` 中按厂家分类的 J-Link 芯片列表
- **稳定性**：J-Link 安全关闭；波形兼容 PySide6 6.x / pyqtgraph 0.14

## 界面说明

v1.0 起界面由 PySide6 完全重写，整体分为 **工具栏**、**左侧连接栏**、**中央显示区**、**底部发送区** 与 **状态栏**。

```text
┌──────────────────────────────────────────────────────────────┐
│ 菜单：连接 | 查看 | 工具 | 帮助                    [主题切换] │
├──────────┬───────────────────────────────────────────────────┤
│ 连接侧栏 │                                                   │
│ 接口模式 │           主显示区（日志 / 终端）                  │
│ 视图模式 │                                                   │
│ 自定义命令│                                                   │
│ 目标信息 │                                                   │
│ 连接按钮 │                                                   │
│ 配置/波形│                                                   │
├──────────┴───────────────────────────────────────────────────┤
│ 发送面板（日志模式）  ASC/HEX | 历史 | 编码 | 换行            │
├──────────────────────────────────────────────────────────────┤
│ 状态栏：连接 | 目标 | RX | TX | 视图 | 过滤状态               │
└──────────────────────────────────────────────────────────────┘
```

### 左侧连接栏

| 区域 | 说明 |
|------|------|
| 接口模式 | **J-Link RTT** / **串口**（需先断开连接再切换） |
| 视图模式 | **日志模式** / **终端模式** |
| 自定义命令 | 打开命令管理对话框，配置名称、内容与 ASC/HEX 发送方式 |
| 目标 | 当前芯片或串口、连接端点摘要 |
| 连接 | 一键连接 / 断开 |
| 配置 / 波形 | 快捷入口 |
| 日志目录 | 打开 `logs/` 保存目录 |

### 主显示区

| 模式 | 行为 |
|------|------|
| **日志模式** | 只读日志视图，支持 BDSCOL 多色、过滤器、暂停跟随、右键清屏 / 滚到底 |
| **终端模式** | 基于 `pyte` 的交互终端，主区直接输入；支持 ANSI 颜色、命令历史、Tab / Ctrl+C |

终端模式下 **底部发送面板自动隐藏**，输入在主显示区完成；日志模式下发送面板用于 ASC / HEX 发送。

### 顶部菜单

| 菜单 | 功能 |
|------|------|
| **连接** | 连接/断开、硬件配置、波形绘制、自定义命令、日志目录 |
| **查看** | 暂停跟随、滚动到底、时间戳、主题切换 |
| **工具** | 查找（`Ctrl+F`）、过滤器设置、启用过滤器、保存全部、实时保存 |
| **帮助** | 检查更新、关于 |

过滤器与表达式在 **工具 → 过滤器** 中配置；状态栏会显示当前过滤状态。

### 配置对话框

分组包括：

- **连接参数**：J-Link（芯片按厂家分组、速度、复位、RTT 搜索范围）或串口（COM、波特率）
- **显示与编码**：utf-8 / asc / hex / gb2312，发送换行符，**界面主题**（深色 / 浅色）
- **波形默认值**：Y 轴范围、曲线名称、轴名称

### 主题与字体

- 主题：`config.json` 中 `ui_theme` 为 `dark` 或 `light`
- 默认字体：Cascadia Mono + 微软雅黑 UI（`config.json` → `font` / `font_size`）

## 功能概览

| 能力 | 说明 |
|------|------|
| J-Link RTT | utf-8 / asc；RTT 通道 0 |
| 串口 | utf-8 / asc / hex；支持中文 |
| 日志模式 | 多色日志、行过滤、暂停跟随、Ctrl+F 搜索、保存全部 |
| 终端模式 | MSH / shell 交互，Enter / Tab / 历史 / Ctrl+C |
| 波形 | 最多 3 条曲线，拖拽、区域统计、CSV 导出 |
| 发送 | ASC / HEX、多行、历史记录、括号注释 |

## 环境要求

- **系统**：Windows 10+
- **Python**：3.9+（源码运行）
- **J-Link**：使用 RTT 时需安装 [SEGGER J-Link](https://www.segger.com/downloads/jlink/)（`JLink_x64.dll`）

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
```

打包（需使用项目 `.venv`）：

```bat
build.bat
```

输出目录：`dist\rtt_t2\`，请运行其中的 `rtt_t2.exe`（需保留整个文件夹）。

**Windows 安装包**（GitHub Releases）：
- `*-windows-x64-setup.exe`：安装向导，**可选择安装目录**（推荐）
- `*-windows-x64.msi`：MSI 安装包（若提供）
- `*-windows-x64.zip`：绿色免安装版

配置与日志保存在 `%LOCALAPPDATA%\rtt_t2\`，升级不会覆盖个人设置。

## 自动更新

启动时若 `config.json` 中 `update_flag` 为 `true`，会通过 **GitHub Releases API** 检测是否有新版本（对比 `flylink-code/rtt_t2` 仓库 tag）。Windows 优先下载 MSI，其次 setup.exe，下载完成后自动打开安装程序。

## 目录结构

```text
rtt_t2/
├─ app/                 PySide6 界面、主题、终端组件
│  ├─ dialogs/          配置、查找、更新、自定义命令
│  ├─ widgets/          日志视图、终端视图、发送面板
│  ├─ services/         日志处理、会话与连接逻辑
│  └─ styles/           dark.qss / light.qss
├─ bds/                 J-Link、串口、波形底层
├─ docs/                开发文档
├─ scripts/             构建与 RTT 诊断脚本
├─ main.py              程序入口
├─ config_manager.py    配置与日志目录
└─ rtt_t2.spec          PyInstaller 配置
```

文档导航：

- 英文说明：[README_EN.md](README_EN.md)
- 源码说明：[docs/source_code.md](docs/source_code.md)
- 目录说明：[docs/project_structure.md](docs/project_structure.md)

## 快速上手

### J-Link RTT

1. 侧栏或工具栏打开 **配置** → 选择芯片（按厂家分组）、速度、是否复位
2. 保存后点击 **连接**
3. 侧栏切换 **日志模式** 或 **终端模式**

> RTT 仅支持通道 0（`SEGGER_RTT_printf(0, ...)`）。

### 串口

1. **配置** 中选择 COM 口与波特率 → 保存 → **连接**

### 日志过滤（仅日志模式）

1. 菜单 **工具 → 过滤器**，输入表达式，如 `TAG=DLOG` 或 `TAG=DLOG&&TAG=BDS`（多关键字用 `&&`）
2. 勾选 **启用过滤器**；勾选 **取反** 则只保留匹配行
3. 也可在 **工具 → 启用过滤器** 快速开关；建议每个关键字长度 ≥ 3

### 自定义命令

侧栏 **自定义命令** → 添加名称、发送内容与 ASC/HEX 类型 → 连接后点击即可发送（终端模式会写入主显示区日志）。

### 波形

1. **配置** 中设置 Y 轴范围、曲线名称（多条用 `&&`，如 `X&&Y&&Z`）
2. 连接后点击 **波形绘制**
3. MCU 按 `TAG=DLOG M*P(x,y,z)\n` 格式发送（见下文）

## 彩色日志（BDSCOL）

```c
#define BDS_COLOR_TAG "BDSCOL"
#define BDS_LOG_COLOR_RED 0xFF3030

SEGGER_RTT_printf(0, BDS_COLOR_TAG "(%d)%s", BDS_LOG_COLOR_RED, "test\n");
```

格式：`BDSCOL(颜色值)你的字符串\n`

## 波形数据格式

```text
TAG=DLOG M*P(x,y,z)\n
```

- 整数：`P=0`
- 浮点：`P` 为小数位数，`x = X * 10^P`（RTT 不支持 `%f`）

单曲线：`M*P(x,0,0)`；双曲线：`M*P(x,y,0)`。

## 芯片配置

`config.json` 中 `jk_chip_catalog` 按厂家列出型号；`jk_chip[0]` 为当前选中芯片。配置对话框保存后会自动更新目录。

## FAQ

### 报错 `Expected to be given a valid DLL`

未找到 J-Link SDK。请安装 SEGGER J-Link，或设置环境变量 `JLINK_SDK` 指向 DLL。

### 芯片识别正常但无 RTT 数据

在 **配置** 中设置 RTT 搜索范围，如 `0x20000000 0x20000`（起始地址 4 字节对齐，`0x` 前缀，空格分隔）。

### 如何添加不支持的芯片

从 J-Link 官方软件复制芯片名，加入 `config.json` 的 `jk_chip_catalog` 对应厂家，或在配置界面保存后自动归类。

### 过滤器在终端模式无效

过滤器仅作用于 **日志模式**；终端模式显示原始字节流（含 ANSI）。

### 打包后提示 `No module named 'pylink'`

请使用项目根目录 `build.bat` 或 `scripts\package_windows.ps1` 打包（会调用 `.venv` 并打入 `pylink` 依赖）。

---

## 致谢

本项目免费开源。若对你有帮助，欢迎 Star。

上游项目：[lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2)
