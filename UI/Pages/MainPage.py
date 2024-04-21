from PyQt5.QtWidgets import  QWidget, QLabel, QGridLayout, QPushButton, QSlider
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

import json

from UI.Recorder.UIRecorder import UIRecorder
from VideoRecorder.Recorder import Recorder

class MainPage(QWidget):
    #Signal object, so we can communicate with the holding UIApp class that a screen change is needed
    #Using this allows easier screen addition since they can be added in more sperate blocks
    switchSignal = pyqtSignal(int)

    def __init__(self, left, top, width, height):
        super().__init__()
        self.recorder = None

        #Import setting from settings.json
        self.reloadSetting()

        #Initialize used variables accross the application
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        
        self.recorder = Recorder(0, self.settings)
        self.uiRecorder = None
        self.videoSizes = [(320,240), (640, 480), (960, 720)]
        
        #Initialize the ui elements
        self.initUI()

    def reloadSetting(self):
        #Utility function, called when we get back to this screen to reload the setttings
        fileHandler = open("Configs/settings.json")
        self.settings = json.load(fileHandler)
        if self.recorder is not None:
            self.recorder.setSettings(self.settings)

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

    def takeScreenshot(self):
        #Calling the take screenshot method from the recorder and checking if it was succesfull
        result = self.recorder.takeScreenshot()
        if result is None:
            return None

    def emitSwitchSignal(self):
        #Couldn't make lambda functions work, so using a normal one
        self.switchSignal.emit(1)

    def changeVolumeLevel(self, level):
        #Function to change the volume level in the ui and in the recorder
        self.volumeLiveLabel.setText(str(level) + "%")
        self.recorder.setAudioVolumeLevel(level/100.0)

    def initUI(self):
        #Initializing the ui elements and their positions
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Create a Label object for the live video feed
        self.livePicture = QLabel(self)
        self.livePicture.resize(160, 120)

        # Create utility and navigation and functional buttons
        self.settingsBtn = QPushButton("Settings")
        self.settingsBtn.clicked.connect(self.emitSwitchSignal)
        self.startBtn = QPushButton("Start recording")
        self.startBtn.clicked.connect(self.startRecorder)
        self.stopBtn = QPushButton("Stop recording")
        self.stopBtn.clicked.connect(self.stopRecorder)
        self.screenshotBtn = QPushButton("Screenshot")
        self.screenshotBtn.clicked.connect(self.takeScreenshot)

        #Create a slider for the volume control
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(100)
        self.volumeSlider.setSingleStep(1)
        self.volumeSlider.setValue(100)
        self.volumeSlider.setMaximumWidth(500)
        self.volumeSlider.setMinimumWidth(300)
        self.volumeSlider.valueChanged.connect(self.changeVolumeLevel)
        self.volumeNameLabel = QLabel(self)
        self.volumeNameLabel.setText("Volume")
        self.volumeLiveLabel = QLabel(self)
        self.volumeLiveLabel.setText("100%")

        # Create box layout, for the positioning of the widgets
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.livePicture, 0, 0, 1, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeNameLabel, 1, 1, 1, 1, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeSlider, 1, 2, 1, 2, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeLiveLabel, 1, 3, 1, 3, Qt.AlignCenter)
        self.mainLayout.addWidget(self.settingsBtn, 2, 1, Qt.AlignCenter)
        self.mainLayout.addWidget(self.startBtn, 2, 2, Qt.AlignCenter)
        self.mainLayout.addWidget(self.stopBtn, 2, 3, Qt.AlignCenter)
        self.mainLayout.addWidget(self.screenshotBtn, 2, 4, Qt.AlignCenter)

        #Finalizing the layout of the main screen
        self.setLayout(self.mainLayout)

        # Show black picture where the video should be
        blackImage = QImage()
        blackImage.load("Presets/Black.png")
        self.setImage(blackImage, manual=True)