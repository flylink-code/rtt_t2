# RTT_T2 v1.0.0

[English](README_EN.md) | 中文

基于 [lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2) fork 的 Windows 嵌入式调试工具，面向 **J-Link RTT** 与 **串口** 日志查看、交互终端、数据发送和波形观察。

> 发行版与更新见 [GitHub Releases](https://github.com/flylink-code/rtt_t2/releases)

## v1.0.0 亮点

- **PySide6 现代化界面**：模块化 `app/` 架构，深色 / 浅色主题
- **双视图模式**：日志模式（彩色 BDSCOL 解析）与终端模式（`pyte` VT100 交互，支持 MSH / ANSI）
- **自定义命令**：侧边栏一键发送常用指令
- **芯片目录**：配置内按厂家分类的常用 J-Link 芯片列表
- **稳定性**：J-Link 安全关闭、波形模块兼容 PySide6 6.x / pyqtgraph 0.14

## 功能概览

| 能力 | 说明 |
|------|------|
| J-Link RTT | 性能优于 RTT Viewer 的部分场景；支持 utf-8 / asc |
| 串口 | utf-8 / asc / hex；支持中文 |
| 日志模式 | 多色日志、行过滤、暂停跟随、Ctrl+F 搜索、保存全部 |
| 终端模式 | 类串口终端交互，Enter / Tab / 历史命令 / Ctrl+C 中断 |
| 波形 | 最多 3 条曲线，拖拽、区域统计、CSV 导出 |
| 发送 | ASC / HEX、多行、历史记录、括号注释 |

## 环境要求

- **系统**：Windows 10+
- **Python**：3.9+（源码运行）
- **J-Link**：使用 RTT 时需安装 [SEGGER J-Link](https://www.segger.com/downloads/jlink/)（提供 `JLink_x64.dll`）

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
```

打包：

```bat
build.bat
```

## 目录结构

```text
rtt_t2/
├─ app/                 PySide6 界面、服务、终端组件
├─ bds/                 J-Link、串口、波形底层
├─ docs/                开发文档
├─ images/              演示图片
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

1. 点击 **配置** → 选择芯片（按厂家分组）、速度、是否复位
2. 保存后点击 **连接**
3. 左侧切换 **日志模式** 或 **终端模式**

> RTT 仅支持通道 0（`SEGGER_RTT_printf(0, ...)`）。

### 串口

1. **配置** 中选择 COM 口与波特率
2. 保存后 **连接**

### 视图模式

| 模式 | 适用场景 |
|------|----------|
| 日志模式 | 彩色标签、过滤器、大量启动日志 |
| 终端模式 | RT-Thread MSH / shell 交互，主区直接输入 |

终端模式下侧边栏 **自定义命令** 可配置快捷指令；底部发送面板在终端模式中自动隐藏。

### 日志过滤（仅日志模式）

1. 顶部 **过滤器** 输入表达式，如 `TAG=DLOG` 或 `TAG=DLOG&&TAG=BDS`
2. 勾选 **启用**；勾选 **取反** 则只保留匹配行
3. 建议每个关键字长度 ≥ 3

### 波形

1. **配置** 中设置 Y 轴范围、曲线名称（多条用 `&&` 分隔，如 `X&&Y&&Z`）
2. 连接硬件后点击 **波形绘制**
3. MCU 按 `TAG=DLOG M*P(x,y,z)\n` 格式发送数据（详见下文）

演示动图（首次加载可能较慢）：

![软件演示](https://gitee.com/bds123/bds_tool/raw/master/images/1.gif)
![波形演示](https://gitee.com/bds123/bds_tool/raw/master/images/2.gif)

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

- 整数：`P=0`，`x,y,z` 为整型值
- 浮点：`P` 为小数位数，`x = X * 10^P`（RTT 不支持 `%f`）

仅一条曲线时发送 `M*P(x,0,0)`；两条为 `M*P(x,y,0)`。

## 芯片配置

`config.json` 中 `jk_chip_catalog` 按厂家列出常用型号；`jk_chip[0]` 为当前选中芯片。配置对话框中也可直接选择，保存后自动写入目录。

手动添加新型号：在对应厂家数组中加入 J-Link 官方芯片名，或保存配置时自动归类到 **其他**。

## FAQ

### 报错 `Expected to be given a valid DLL`

未找到 J-Link SDK。请安装 SEGGER J-Link 软件，或设置环境变量 `JLINK_SDK` 指向 DLL 路径。

### 芯片识别正常但无 RTT 数据

在 **配置** 中设置 `_SEGGER_RTT` 搜索范围，例如 `0x20000000 0x20000`（起始地址 4 字节对齐，十六进制以 `0x` 开头，两值空格分隔）。也可查看 map 文件或芯片手册 RAM 区域。

### 如何添加不支持的芯片

从 J-Link 官方软件复制芯片名，加入 `config.json` 的 `jk_chip_catalog` 对应厂家下，或在配置界面选择后保存。

### 过滤器在终端模式无效

过滤器仅作用于 **日志模式**；终端模式显示原始字节流（含 ANSI）。

---

## 致谢

本项目免费开源。若对你有帮助，欢迎 Star。

上游项目：[lh-hg/rtt_t2](https://github.com/lh-hg/rtt_t2)
