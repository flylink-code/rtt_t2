# 源码与开发说明

本文档面向需要维护、调试或二次开发 `RTT_T2` 的工程师，重点说明开发环境、关键依赖、第三方库修改点以及打包方式。

## 开发环境

- IDE：PyCharm
- Python：3.9
- 目标平台：Windows

## 关键依赖

- `PySimpleGUI` `4.53.0`
  用于主界面搭建。

- `pylink` `1.1.0`
  用于连接 J-Link 并访问 RTT 功能。

- `pyserial` `3.5`
  用于串口收发。

- `pyqtgraph` `0.12.4`
  用于实时波形显示。该库依赖 `PyQt`，版本匹配关系需要按上游要求选择。

## 代码结构概览

- `rtt_t2.py`
  主入口，负责界面、线程、日志流、RTT/串口连接与交互。

- `config_manager.py`
  负责默认配置、配置文件加载保存、日志目录初始化。

- `text_searcher.py`
  封装日志区域文本查找功能。

- `bds/bds_jlink.py`
  J-Link 与 RTT 相关实现。

- `bds/bds_serial.py`
  串口通信相关实现。

- `bds/bds_waveform.py`
  波形显示逻辑。

- `rtt_diag.py`
  诊断 RTT 控制块和通道状态的辅助脚本。

## 第三方库修改点

### PySimpleGUI

为了获取多行控件滚动条位置，需要在 `PySimpleGUI.py` 中增加如下方法，可放在已有的 `set_vscroll_position()` 后面：

```python
def get_vscroll_position(self):
    """
    Get the relative position of the scrollbar

    :return: (y1,y2)
    :rtype: tuple
    """
    try:
        return self.Widget.yview()
    except Exception as e:
        print('Warning get the vertical scroll (yview failed)')
        print(e)
        return None
```

### pyqtgraph

为了捕获鼠标按下和松开事件，从而支持更细致的波形拖拽交互，需要在 `GraphicsScene.py` 中补充信号和事件发送逻辑。

1. 增加两个信号：

```python
# 已有的
sigMouseHover = QtCore.Signal(object)
sigMouseMoved = QtCore.Signal(object)
sigMouseClicked = QtCore.Signal(object)

# 新增的
sigMousePress = QtCore.Signal(object)
sigMouseRelease = QtCore.Signal(object)
```

2. 在事件函数中发送信号：

```python
def mousePressEvent(self, ev):
    super().mousePressEvent(ev)
    self.sigMousePress.emit(ev)
    .......

def mouseReleaseEvent(self, ev):
    self.sigMouseRelease.emit(ev)
    .......
```

## 打包方式

项目使用 `PyInstaller 5.1` 打包。

### 推荐入口

在项目根目录运行：

```bat
build.bat
```

该命令会转发到：

```bat
scripts\build.bat
```

### 实际打包配置

`scripts/build.bat` 内部调用：

```bat
pyinstaller rtt_t2.spec
```

`rtt_t2.spec` 中已包含：

- 入口脚本：`rtt_t2.py`
- 图标：`tool.ico`
- 排除模块：`scipy`
- 窗口模式：`console=False`

## 维护建议

- 运行期文件优先保持根目录相对路径稳定，避免影响 `config.json`、`aaa_log/`、图标与资源查找。
- 构建、测试、诊断类脚本尽量集中到专用目录，并在 `docs/` 中记录用途。
- 如果后续继续扩展功能，建议优先拆分 `rtt_t2.py` 中的界面、通信和升级逻辑，降低单文件维护成本。
