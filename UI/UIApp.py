from PyQt5.QtWidgets import  QWidget, QStackedWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSlot

from win32api import GetSystemMetrics

from UI.Pages.MainPage import MainPage
from UI.Pages.SettingsPage import SettingsPage

class UIApp(QWidget):
    def __init__(self):
        super().__init__()

        #Initialize starting metrics, for fullscreen
        self.title = 'Video Recorder'
        self.left = int(GetSystemMetrics(0)/10)
        self.top = int(GetSystemMetrics(1)/10)
        self.width = int(GetSystemMetrics(0) - GetSystemMetrics(0)/5)
        self.height = int(GetSystemMetrics(1) - GetSystemMetrics(1)/5)

        #Setting up the QStackedWidget for widget swtich
        self.stackedWidget = QStackedWidget(self)
        self.initUI()

    @pyqtSlot(int)
    def changeScreen(self, index):
        #Utility function to switch between screen

        #Checking if the index is out of bounds
        if index < 0 or index > 1:
            print("Invalid swtch try, index is: ", index)
            return
        
        #Reload the settings in the main page and settings page, when we switch back
        if index == 1:
            self.settingsPage.reloadSetting()
        else:
            self.mainPage.reloadSetting()

        #Switching between the screens
        self.stackedWidget.setCurrentIndex(index)
        
    def initUI(self):
        #Setting up the title and the geometry
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        #Setting up the main page of the application
        self.mainPage = MainPage(self.left, self.top, self.width, self.height)
        self.mainPage.switchSignal.connect(self.changeScreen)
        self.stackedWidget.addWidget(self.mainPage)

        #Setting up the settings page of the application
        self.settingsPage = SettingsPage(self.left, self.top, self.width, self.height)
        self.settingsPage.switchSignal.connect(self.changeScreen)
        self.stackedWidget.addWidget(self.settingsPage)

        #Setting up the current screen which should be showed
        self.stackedWidget.setCurrentIndex(0)

        #Setting up a layout for the main application
        self.mainLayout = QHBoxLayout()
        self.mainLayout.addWidget(self.stackedWidget, Qt.AlignCenter)
        self.setLayout(self.mainLayout)

        #Show the current widget (the current screen)
        self.show()