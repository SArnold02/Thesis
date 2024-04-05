import sys
from PyQt5.QtWidgets import QApplication

from UI.UIApp import UIApp

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = UIApp()
    sys.exit(app.exec_())