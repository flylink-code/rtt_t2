# 项目目录说明

本文档说明 `rtt_t2` 目录中各文件和子目录的职责，方便后续维护、打包和二次开发。

## 目录分层

### 运行期核心文件

- `main.py`
  主程序入口，启动 `app/` 中的 PySide6 应用。

- `app/`
  GUI、RTT/串口收发、日志显示、升级检查等主流程。

- `config_manager.py`
  配置文件与日志目录管理，负责 `config.json` 与 `aaa_log/` 的创建和读写。

- `app/text_search.py`
  日志区域文本查找（PySide6 实现）。

- `bds/`
  底层通信与波形绘制相关模块，包括 J-Link、串口、波形和辅助工具。

- `config.json`
  运行期配置文件，保存串口、J-Link、字体、波形和过滤器等参数。

### 资源文件

- `images/`
  README 和文档中使用的演示图片、动图资源。

- `tool.ico`
  Windows 打包图标。

- `tool.png`
  项目展示图资源。

### 文档

- `README.md`
  面向使用者的总入口文档，包含功能介绍、使用说明和 FAQ。

- `docs/source_code.md`
  面向开发者的源码和依赖说明。

- `docs/project_structure.md`
  当前文档，用于说明目录结构与文件职责。

### 开发与构建辅助

- `scripts/build.bat`
  统一的打包脚本入口，实际执行 PyInstaller。

- `build.bat`
  根目录兼容入口，转发到 `scripts/build.bat`，方便保留原有使用方式。

- `rtt_t2.spec`
  PyInstaller 打包配置。

- `scripts/rtt_diag.py`
  RTT 诊断脚本，用于排查 RTT 控制块、缓冲区和 J-Link 连接问题。

## 建议的维护原则

- 运行期依赖的文件继续保留在根目录，避免破坏现有相对路径逻辑。
- 构建脚本、诊断脚本、测试脚本优先放到 `scripts/` 或 `docs/` 中说明其用途。
- 新增资源文件时，优先放入 `images/` 或新的专用资源目录，不要散落在根目录。
- 新增开发说明、适配记录、排障文档时，统一放到 `docs/`。
