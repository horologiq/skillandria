import sys

from PyQt5.QtWidgets import QApplication
from skillandria.videoplayer import VideoPlayer


class Main:
    app = QApplication(sys.argv)
    player = VideoPlayer()
    sys.exit(app.exec_())
