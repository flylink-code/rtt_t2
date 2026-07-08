import multiprocessing
import os
import sys

# pyqtgraph / waveform subprocess should use the same Qt binding.
os.environ.setdefault('PYQTGRAPH_QT_LIB', 'PySide6')

from app.application import run


def main():
    multiprocessing.freeze_support()
    sys.exit(run())


if __name__ == '__main__':
    main()
