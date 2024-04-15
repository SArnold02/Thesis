from PyQt5.QtWidgets import  QWidget, QGridLayout, QPushButton, QLineEdit, QLabel
from PyQt5.QtCore import Qt, pyqtSignal

import json
import tkinter
from tkinter import filedialog

class SettingsPage(QWidget):
    #Signal object, so we can communicate with the holding UIApp class that a screen change is needed
    #Using this allows easier screen addition since they can be added in more sperate blocks
    switchSignal = pyqtSignal(int)

    def __init__(self, left, top, width, height):
        super().__init__()

        #Import setting from settings.json
        self.filePath = None
        self.reloadSetting()

        #Initialize used variables accross the application
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        #Initialize the ui elements
        self.initUI()

    def reloadSetting(self):
        #Utility function, called when we get back to this screen to reload the setttings
        fileHandler = open("Configs/settings.json")
        self.settings = json.load(fileHandler)
        if self.filePath is not None:
            self.filePath.setText(self.settings["savePath"])

    def emitSwitchSignal(self):
        #Couldn't make lambda functions work, so using a normal one
        self.switchSignal.emit(0)

    def saveChanges(self):
        #Functions to save every change done in the settings
        with open("Configs/settings.json", "w") as outfile:
            json.dump(self.settings, outfile)

        self.emitSwitchSignal()

    def changeFilePath(self):
        #Function which changes the file path chosen by the windows file explorer
        #Getting the file path from the explorer
        tkinter.Tk().withdraw()
        filePath = filedialog.askdirectory()
        self.settings["savePath"] = filePath
        self.filePath.setText(filePath)

    def changeScreenshotFilePath(self):
        #Function which changes the screenshot file path chosen by the windows file explorer
        #Getting the file path from the explorer
        tkinter.Tk().withdraw()
        filePath = filedialog.askdirectory()
        self.settings["screenshotPath"] = filePath
        self.screenshotFilePath.setText(filePath)

    def initUI(self):
        #Initializing the ui elements and their positions
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create utility and navigation buttons
        self.backBtn = QPushButton("Back")
        self.backBtn.clicked.connect(self.emitSwitchSignal)
        self.backBtn.setFixedWidth(100)
        self.saveBtn = QPushButton("Save")
        self.saveBtn.clicked.connect(self.saveChanges)
        self.saveBtn.setFixedWidth(100)

        #Create text widgets for the menu options
        self.filePath = QLineEdit()
        self.filePath.setText(self.settings["savePath"])
        self.filePath.setReadOnly(True)
        self.filePath.setFixedWidth(300)
        self.filePathLabel = QLabel()
        self.filePathLabel.setText("Video Save File Path")
        self.filePathLabel.setBuddy(self.filePath)
        self.filePathLabel.setFixedHeight(100)
        self.filePathBtn = QPushButton("Choose Path")
        self.filePathBtn.clicked.connect(self.changeFilePath)
        self.filePathBtn.setFixedWidth(100)

        #Create text widgets for the screenshot menu options
        self.screenshotFilePath = QLineEdit()
        self.screenshotFilePath.setText(self.settings["screenshotPath"])
        self.screenshotFilePath.setReadOnly(True)
        self.screenshotFilePath.setFixedWidth(300)
        self.screenshotFilePathLabel = QLabel()
        self.screenshotFilePathLabel.setText("Screenshot Save File Path")
        self.screenshotFilePathLabel.setBuddy(self.screenshotFilePath)
        self.screenshotFilePathLabel.setFixedHeight(100)
        self.screenshotFilePathBtn = QPushButton("Choose Path")
        self.screenshotFilePathBtn.clicked.connect(self.changeScreenshotFilePath)
        self.screenshotFilePathBtn.setFixedWidth(100)

        # Create box layout, for the positioning of the widgets
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.filePathLabel, 0, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.filePath, 1, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.filePathBtn, 1, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.screenshotFilePathLabel, 2, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.screenshotFilePath, 3, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.screenshotFilePathBtn, 3, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.saveBtn, 4, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.backBtn, 4, 1, Qt.AlignCenter)

        #Finalizing the layout of the main screen
        self.setLayout(self.mainLayout)