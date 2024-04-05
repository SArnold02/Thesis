from PyQt5.QtWidgets import  QWidget, QLabel, QGridLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

import json

from UI.Recorder.UIRecorder import UIRecorder
from VideoRecorder.Recorder import Recorder

class SettingsPage(QWidget):
    #Signal object, so we can communicate with the holding UIApp class that a screen change is needed
    #Using this allows easier screen addition since they can be added in more sperate blocks
    switchSignal = pyqtSignal(int)

    def __init__(self, left, top, width, height):
        super().__init__()

        #Import setting from settings.json
        fileHandler = open("Configs/settings.json")
        self.settings = json.load(fileHandler) 

        #Initialize used variables accross the application
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.recorder = Recorder(0, self.settings)
        self.uiRecorder = None
        self.videoSizes = [(320,240), (640, 480), (960, 720)]
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image, manual=False):
        if self.uiRecorder is None and not manual:
            return
        
        currentWidth = self.size().width()
        currentGeometry = self.getCurrentVideoGeometry(currentWidth)

        rescaledImage = image.scaled(currentGeometry[0], currentGeometry[1], Qt.KeepAspectRatio)
        self.livePicture.setPixmap(QPixmap.fromImage(rescaledImage))

    def getCurrentVideoGeometry(self, width):
        currentIndex = 0
        for size in self.videoSizes[1:]:
            if (width > size[0] + 100):
                currentIndex += 1
            else: break
        return self.videoSizes[currentIndex]
    
    def startRecorder(self):
        #Checking if the uiRecorder has already been started, so there is not two running at the same time
        if self.uiRecorder is not None:
            return
        
        #Connect the signals and start the recorder
        self.uiRecorder = UIRecorder(0, self.recorder)
        self.uiRecorder.changePixmap.connect(self.setImage)
        self.uiRecorder.start()

    def stopRecorder(self):
        #Check if the uiRecorder has already been stopped
        if self.uiRecorder is None:
            return

        #Stopping the Recorder        
        self.uiRecorder.changePixmap.disconnect(self.setImage)
        self.uiRecorder.stop()
        self.uiRecorder.wait()
        self.uiRecorder = None

        #Setting the video feed back to a black image
        blackImage = QImage()
        blackImage.load("Presets/Black.png")
        self.setImage(blackImage, manual=True)

    def emitSwitchSignal(self):
        #Couldn't make lambda functions work, so using a normal one
        self.switchSignal.emit(0)

    def initUI(self):
        #Initializing the ui elements and their positions
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create a Label object for the live video feed
        self.livePicture = QLabel(self)
        self.livePicture.resize(160, 120)

        # Create utility and navigation buttons
        self.settingsBtn = QPushButton("Settings")
        self.settingsBtn.clicked.connect(self.emitSwitchSignal)
        self.startBtn = QPushButton("Stasdng")
        self.startBtn.clicked.connect(self.startRecorder)
        self.stopBtn = QPushButton("Stop recording")
        self.stopBtn.clicked.connect(self.stopRecorder)

        # Create box layout, for the positioning of the widgets
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.livePicture, 0, 0, 1, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.settingsBtn, 1, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.startBtn, 1, 1, Qt.AlignCenter)
        self.mainLayout.addWidget(self.stopBtn, 1, 2, Qt.AlignCenter)

        #Finalizing the layout of the main screen
        self.setLayout(self.mainLayout)

        # Show black picture where the video should be
        blackImage = QImage()
        blackImage.load("Presets/Black.png")
        self.setImage(blackImage, manual=True)