from PyQt5.QtWidgets import  QWidget, QGridLayout, QPushButton, QLineEdit, QLabel, QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCursor

import cv2
import pyaudio
import json
import tkinter
from tkinter import filedialog

class SettingsPage(QWidget):
    #Signal object, so we can communicate with the holding UIApp class that a screen change is needed
    #Using this allows easier screen addition since they can be added in more sperate blocks
    switchSignal = pyqtSignal(int)
    initialized = False

    def __init__(self, left, top, width, height):
        super().__init__()

        #Initialize used variables accross the application
        self.left = left
        self.top = top
        self.width = width
        self.height = height

        #Import setting from settings.json
        self.reloadSetting()

        #Initialize the ui elements
        self.initUI()
        self.initialized = True

    def getAudioDeviceList(self):
        #Get the list of audio devices for option to swap them
        p = pyaudio.PyAudio()
        info = p.get_host_api_info_by_index(0)
        deviceNumber = info.get('deviceCount')
        returnArray = []

        for i in range(deviceNumber):
            if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
                returnArray.append((i, p.get_device_info_by_host_api_device_index(0, i).get('name')))

        p.terminate()
        return returnArray

    def getVideoDeviceList(self):
        #Since there is no built-in method to acquire the list of video capture devices, I loop through them until I get an error, meaning no available device
        index = 0
        returnArray = []
        while True:
            device = cv2.VideoCapture(index)
            try:
                device.getBackendName()
                returnArray.append((index))
            except:
                #Leave the loop id the current device backend name could not be gotten
                break
            
            device.release()
            index += 1

        return returnArray

    def reloadSetting(self):
        #Utility function, called when we get back to this screen to reload the setttings
        fileHandler = open("Configs/settings.json")
        self.settings = json.load(fileHandler)
        fileHandler.close()
        if self.initialized:
            self.filePath.setText(self.settings["savePath"])
            self.screenshotFilePath.setText(self.settings["screenshotPath"])

        #Get the available video and audio devices
        self.videoDeviceList = self.getVideoDeviceList()
        self.audioDeviceList = self.getAudioDeviceList()

        #Reload the items for the selections lists
        if self.initialized:
            self.cameraSelectionBox.currentIndexChanged.disconnect(self.changeCameraSelection)
            self.cameraSelectionBox.clear()
            for device in self.videoDeviceList:
                self.cameraSelectionBox.addItem("Camera " + str(device))
            self.cameraSelectionBox.setCurrentIndex(self.videoDeviceList.index(int(self.settings["cameraChoice"])))
            self.cameraSelectionBox.currentIndexChanged.connect(self.changeCameraSelection)

            self.audioSelectionBox.currentIndexChanged.disconnect(self.changeAudioSelection)
            self.audioSelectionBox.clear()
            for device in self.audioDeviceList:
                self.audioSelectionBox.addItem(str(device[0]) + " - " + device[1])
            currentIndex = 0
            for i, device in enumerate(self.audioDeviceList):
                if device[0] == self.settings["audioChoice"]:
                    currentIndex = i
                    break
            self.audioSelectionBox.setCurrentIndex(currentIndex)
            self.audioSelectionBox.currentIndexChanged.connect(self.changeAudioSelection)

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

    def changeCameraSelection(self, index):
        #Function to save to the settings variable the currrently selected camera choide
        try:
            self.settings["cameraChoice"] = self.cameraSelectionBox[index]
        except Exception:
            return

    def changeAudioSelection(self, index):
        #Function to save to the settings variable the currrently selected audio device choice
        try:
            self.settings["audioChoice"] = self.audioDeviceList[index][0]
        except Exception:
            return

    def initUI(self):
        #Initializing the ui elements and their positions
        self.setGeometry(self.left, self.top, self.width, self.height)

        #Creating stylesheets
        buttonStyleSheet = """
            QPushButton {
                background-color: SlateBlue; 
                border: none;
                color: white;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: SteelBlue; 
                cursor: pointer;
            }
            """
        dropDownListStyleSheet = """
            QComboBox {
                border: 1px solid SlateBlue;
                border-radius: 5px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
            }
            QComboBox::drop-down {
                border: none;
            }
            """
        labelStyleSheet = """
            QLabel {
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                padding: 10px;
            }
            """
        lineEditStyleSheet = """
            QLineEdit {
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                padding: 10px;
            }
            """

        # Create utility and navigation buttons
        self.backBtn = QPushButton("Back")
        self.backBtn.clicked.connect(self.emitSwitchSignal)
        self.backBtn.setFixedWidth(100)
        self.backBtn.setStyleSheet(buttonStyleSheet)
        self.backBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.saveBtn = QPushButton("Save")
        self.saveBtn.clicked.connect(self.saveChanges)
        self.saveBtn.setFixedWidth(100)
        self.saveBtn.setStyleSheet(buttonStyleSheet)
        self.saveBtn.setCursor(QCursor(Qt.PointingHandCursor))

        #Create text widgets for the menu options
        self.filePath = QLineEdit()
        self.filePath.setText(self.settings["savePath"])
        self.filePath.setReadOnly(True)
        self.filePath.setFixedWidth(400)
        self.filePath.setStyleSheet(lineEditStyleSheet)
        self.filePathLabel = QLabel()
        self.filePathLabel.setText("Video Save File Path")
        self.filePathLabel.setBuddy(self.filePath)
        self.filePathLabel.setFixedHeight(100)
        self.filePathLabel.setStyleSheet(labelStyleSheet)
        self.filePathBtn = QPushButton("Choose Path")
        self.filePathBtn.clicked.connect(self.changeFilePath)
        self.filePathBtn.setFixedWidth(150)
        self.filePathBtn.setStyleSheet(buttonStyleSheet)
        self.filePathBtn.setCursor(QCursor(Qt.PointingHandCursor))

        #Create text widgets for the screenshot menu options
        self.screenshotFilePath = QLineEdit()
        self.screenshotFilePath.setText(self.settings["screenshotPath"])
        self.screenshotFilePath.setReadOnly(True)
        self.screenshotFilePath.setFixedWidth(400)
        self.screenshotFilePath.setStyleSheet(lineEditStyleSheet)
        self.screenshotFilePathLabel = QLabel()
        self.screenshotFilePathLabel.setText("Screenshot Save File Path")
        self.screenshotFilePathLabel.setBuddy(self.screenshotFilePath)
        self.screenshotFilePathLabel.setFixedHeight(100)
        self.screenshotFilePathLabel.setStyleSheet(labelStyleSheet)
        self.screenshotFilePathBtn = QPushButton("Choose Path")
        self.screenshotFilePathBtn.clicked.connect(self.changeScreenshotFilePath)
        self.screenshotFilePathBtn.setFixedWidth(150)
        self.screenshotFilePathBtn.setStyleSheet(buttonStyleSheet)
        self.screenshotFilePathBtn.setCursor(QCursor(Qt.PointingHandCursor))

        #Creating widgets for the video camera selection option
        self.cameraSelectionBox = QComboBox(self)
        for device in self.videoDeviceList:
            self.cameraSelectionBox.addItem("Camera " + str(device))
        self.cameraSelectionBox.setFixedWidth(400)
        self.cameraSelectionBox.setCurrentIndex(self.videoDeviceList.index(int(self.settings["cameraChoice"])))
        self.cameraSelectionBox.currentIndexChanged.connect(self.changeCameraSelection)
        self.cameraSelectionLabel = QLabel()
        self.cameraSelectionLabel.setText("Select Camera")
        self.cameraSelectionLabel.setBuddy(self.cameraSelectionBox)
        self.cameraSelectionLabel.setFixedHeight(100)
        self.cameraSelectionLabel.setStyleSheet(labelStyleSheet)
        self.cameraSelectionBox.setStyleSheet(dropDownListStyleSheet)
        self.cameraSelectionBox.setCursor(QCursor(Qt.PointingHandCursor))

        #Creating widgets for the video audio selection option
        self.audioSelectionBox = QComboBox(self)
        for device in self.audioDeviceList:
            self.audioSelectionBox.addItem(str(device[0]) + " - " + device[1])
        self.audioSelectionBox.setFixedWidth(400)
        
        currentIndex = 0
        for i, device in enumerate(self.audioDeviceList):
            if device[0] == self.settings["audioChoice"]:
                currentIndex = i
                break

        self.audioSelectionBox.setCurrentIndex(currentIndex)
        self.audioSelectionBox.currentIndexChanged.connect(self.changeAudioSelection)
        self.audioSelectionBox.setStyleSheet(dropDownListStyleSheet)
        self.audioSelectionBox.setCursor(QCursor(Qt.PointingHandCursor))
        self.audioSelectionLabel = QLabel()
        self.audioSelectionLabel.setText("Select Audio")
        self.audioSelectionLabel.setBuddy(self.audioSelectionBox)
        self.audioSelectionLabel.setFixedHeight(100)
        self.audioSelectionLabel.setStyleSheet(labelStyleSheet)

        # Create box layout, for the positioning of the widgets
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.filePathLabel, 0, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.filePath, 1, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.filePathBtn, 1, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.screenshotFilePathLabel, 2, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.screenshotFilePath, 3, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.screenshotFilePathBtn, 3, 1, Qt.AlignLeft)
        self.mainLayout.addWidget(self.cameraSelectionLabel, 4, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.cameraSelectionBox, 5, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.audioSelectionLabel, 6, 0, 1, 0, Qt.AlignHCenter)
        self.mainLayout.addWidget(self.audioSelectionBox, 7, 0, Qt.AlignRight)
        self.mainLayout.addWidget(self.saveBtn, 8, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.backBtn, 8, 1, Qt.AlignCenter)

        #Finalizing the layout of the main screen
        self.setLayout(self.mainLayout)