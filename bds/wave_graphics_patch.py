from pyqtgraph.Qt import QtCore


def apply_graphics_scene_mouse_signals():
    from pyqtgraph.GraphicsScene.GraphicsScene import GraphicsScene

    if getattr(GraphicsScene, '_rtt_mouse_patch', False):
        return

    GraphicsScene.sigMousePress = QtCore.Signal(object)
    GraphicsScene.sigMouseRelease = QtCore.Signal(object)

    original_press = GraphicsScene.mousePressEvent
    original_release = GraphicsScene.mouseReleaseEvent

    def mouse_press_event(self, event):
        original_press(self, event)
        self.sigMousePress.emit(event)

    def mouse_release_event(self, event):
        original_release(self, event)
        self.sigMouseRelease.emit(event)

    GraphicsScene.mousePressEvent = mouse_press_event
    GraphicsScene.mouseReleaseEvent = mouse_release_event
    GraphicsScene._rtt_mouse_patch = True
