import sys

from PyQt5.QtWidgets import QApplication
from videoplayer import VideoPlayer

config_file = "config.ini"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = VideoPlayer()
    sys.exit(app.exec_())
