import sys

from PyQt6.QtWidgets import QApplication

from skillandria.courses import CourseWindow

class Main:
    app = QApplication(sys.argv)
    main_window = CourseWindow()
    main_window.show()
    sys.exit(app.exec())
