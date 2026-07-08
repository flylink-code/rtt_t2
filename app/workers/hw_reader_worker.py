import threading
import time

from PySide6.QtCore import QThread


class HwReaderWorker(QThread):
    def __init__(self, hw_obj, thread_lock, parent=None):
        super().__init__(parent)
        self._hw_obj = hw_obj
        self._thread_lock = thread_lock
        self._running = True

    def set_hw_obj(self, hw_obj):
        self._hw_obj = hw_obj

    def run(self):
        while self._running:
            try:
                self._thread_lock.acquire()
                self._hw_obj.hw_read()
                interval = self._hw_obj.get_read_data_time_interval_s()
            finally:
                self._thread_lock.release()
            time.sleep(interval)

    def stop(self):
        self._running = False
        self.wait(2000)


thread_lock = threading.Lock()
