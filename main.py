import main_window
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = main_window.Window()
    window.show()
    sys.exit(app.exec_())
