from PyQt5.QtWidgets import  QWidget, QLabel, QGridLayout, QPushButton, QSlider, QCheckBox
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap, QCursor

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
        
        self.recorder = Recorder(self.settings)
        self.uiRecorder = None
        self.videoSizes = [(320,240), (640, 480), (960, 720)]

        self.maxVolume = 100
        self.lastVolume = self.maxVolume
        self.currentVolume = self.maxVolume
        self.gestureCounter = 0
        
        #Initialize the ui elements
        self.initUI()

    def reloadSetting(self):
        #Utility function, called when we get back to this screen to reload the setttings
        fileHandler = open("Configs/settings.json")
        self.settings = json.load(fileHandler)
        if self.recorder is not None:
            self.recorder.setSettings(self.settings)

    def getCurrentVideoGeometry(self, width):
        currentIndex = 0
        for size in self.videoSizes[1:]:
            if (width > size[0] + 100):
                currentIndex += 1
            else: break
        return self.videoSizes[currentIndex]

    @pyqtSlot(QImage)
    def setImage(self, image, manual=False):
        if self.uiRecorder is None and not manual:
            return
        
        currentWidth = self.size().width()
        currentGeometry = self.getCurrentVideoGeometry(currentWidth)

        rescaledImage = image.scaled(currentGeometry[0], currentGeometry[1], Qt.KeepAspectRatio)
        self.livePicture.setPixmap(QPixmap.fromImage(rescaledImage))

    @pyqtSlot(int)
    def setAudioLevel(self, levelChange):
        #A bug calls the emit signal twice, so every second gesture has to be skipped        
        self.gestureCounter += 1
        if self.gestureCounter == 2:
            self.gestureCounter = 0
            return

        #Check the different possible changes, 0 - mute toggle, negative - voicedown, positive - voiceup
        if levelChange == 0:
            if self.currentVolume != 0:
                self.lastVolume = self.currentVolume
                self.volumeSlider.setValue(0)
            else:
                self.volumeSlider.setValue(self.lastVolume)
        elif self.currentVolume + levelChange >= 0 and self.currentVolume + levelChange <= self.maxVolume:
            self.volumeSlider.setValue(self.currentVolume + levelChange)

    @pyqtSlot(int)
    def errorHandling(self, returnValue):
        # Depending on the returnValue handle the possible errors
        if returnValue == 1:
                self.stopRecorderUtil("Invalid camera settings, recording cannot be started!")
        elif returnValue == 2:
                self.stopRecorderUtil("No video path found, cannot start recording!")
        elif returnValue == 3:
                self.stopRecorderUtil("Invalid audio settings recording cannot be started!")
        elif returnValue == 4:
                self.stopRecorderUtil("Video or Audio input error!")

    def emitSwitchSignal(self):
        #Couldn't make lambda functions work, so using a normal one
        if self.uiRecorder is not None:
            self.messageLabel.setText("Cannot switch while recording!")
            QTimer.singleShot(2000, lambda : self.messageLabel.setText(""))
            return
        self.switchSignal.emit(1)

    def switchAISupport(self, checkBox):
        #Couldn't make lambda functions work, so using a normal one
        if self.uiRecorder is not None:
            self.uiRecorder.switchAISupport(checkBox != 0)

    def takeScreenshot(self):
        #Calling the take screenshot method from the recorder and checking if it was succesfull
        if self.uiRecorder is None:
            return
        
        text = "Screenshot taken!"
        result = self.recorder.takeScreenshot()
        if result is None:
            text = "Invalid screenshot path!"
        
        self.messageLabel.setText(text)
        QTimer.singleShot(2000, lambda : self.messageLabel.setText(""))

    def changeVolumeLevel(self, level):
        #Function to change the volume level in the ui and in the recorder
        self.volumeLiveLabel.setText(str(level) + "%")
        self.recorder.setAudioVolumeLevel(level/100.0)
        self.currentVolume = level
    
    def startRecorder(self):
        #Checking if the uiRecorder has already been started, so there is not two running at the same time
        if self.uiRecorder is not None:
            return
        
        #Connect the signals and start the recorder
        self.messageLabel.setText("Recording is being started!")
        QTimer.singleShot(2000, lambda : self.messageLabel.setText(""))

        self.uiRecorder = UIRecorder(0, self.recorder)
        self.uiRecorder.changePixmap.connect(self.setImage)
        self.uiRecorder.soundChangeSignal.connect(self.setAudioLevel)
        self.uiRecorder.errorSignal.connect(self.errorHandling)
        self.uiRecorder.switchAISupport(self.aiSupport.isChecked())
        self.uiRecorder.start()

    def stopRecorderUtil(self, text = "Recording is stopping, the video save might take a few moments, dont turn off!"):
        #In order for qt to load the message before waiting for ht uiRecorder to finish a small delay is inserted
        if self.uiRecorder is None:
            return
        self.messageLabel.setText(text)
        QTimer.singleShot(1000, lambda : self.stopRecorder())

    def stopRecorder(self):
        #Check if the uiRecorder has already been stopped
        QTimer.singleShot(5000, lambda : self.messageLabel.setText(""))

        #Stopping the Recorder        
        self.uiRecorder.changePixmap.disconnect(self.setImage)
        self.uiRecorder.soundChangeSignal.disconnect(self.setAudioLevel)
        self.uiRecorder.errorSignal.disconnect(self.errorHandling)
        self.uiRecorder.stop()
        self.uiRecorder.wait()
        self.uiRecorder = None

        #Setting the video feed back to a black image
        blackImage = QImage()
        blackImage.load("Presets/Black.png")
        self.setImage(blackImage, manual=True)

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
            }
            """
        aiSupportStyleSheet = """
            QCheckBox {
                background-color: SlateBlue; 
                border: none;
                color: white;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                border-radius: 12px;
                padding: 10px;
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
        sliderStyleSheet = """
            QSlider::groove:horizontal {
                border: 1px solid SlateBlue;
                height: 6px;
            }
            QSlider::handle:horizontal {
                background: SlateBlue;
                width: 10px;
                height: 10px;
                margin: -5px -1px;
                border-radius: 5px;
                border: 1px solid SlateBlue;
            }
            QSlider::sub-page:horizontal {
                background: SlateBlue
            }
            """

        # Create a Label object for the live video feed
        self.livePicture = QLabel(self)
        self.livePicture.resize(160, 120)

        # Create utility and navigation and functional buttons and labels
        self.messageLabel = QLabel(self)
        # self.messageLabel.resize(160, 50)
        self.settingsBtn = QPushButton("Settings")
        self.settingsBtn.clicked.connect(self.emitSwitchSignal)
        self.settingsBtn.setStyleSheet(buttonStyleSheet)
        self.settingsBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.startBtn = QPushButton("Start recording")
        self.startBtn.clicked.connect(self.startRecorder)
        self.startBtn.setStyleSheet(buttonStyleSheet)
        self.startBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.stopBtn = QPushButton("Stop recording")
        self.stopBtn.clicked.connect(lambda: self.stopRecorderUtil())
        self.stopBtn.setStyleSheet(buttonStyleSheet)
        self.stopBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.screenshotBtn = QPushButton("Screenshot")
        self.screenshotBtn.clicked.connect(self.takeScreenshot)
        self.screenshotBtn.setStyleSheet(buttonStyleSheet)
        self.screenshotBtn.setCursor(QCursor(Qt.PointingHandCursor))
        self.aiSupport = QCheckBox("AI Support")
        self.aiSupport.setChecked(False)
        self.aiSupport.stateChanged.connect(self.switchAISupport)
        self.aiSupport.setStyleSheet(aiSupportStyleSheet)

        #Create a slider for the volume control
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setMinimum(0)
        self.volumeSlider.setMaximum(self.maxVolume)
        self.volumeSlider.setSingleStep(1)
        self.volumeSlider.setValue(self.maxVolume)
        self.volumeSlider.setMaximumWidth(500)
        self.volumeSlider.setMinimumWidth(300)
        self.volumeSlider.valueChanged.connect(self.changeVolumeLevel)
        self.volumeSlider.setStyleSheet(sliderStyleSheet)
        self.volumeNameLabel = QLabel(self)
        self.volumeNameLabel.setText("Volume")
        self.volumeNameLabel.setStyleSheet(labelStyleSheet)
        self.volumeLiveLabel = QLabel(self)
        self.volumeLiveLabel.setText("100%")
        self.volumeLiveLabel.setStyleSheet(labelStyleSheet)

        # Create box layout, for the positioning of the widgets
        self.mainLayout = QGridLayout()
        self.mainLayout.addWidget(self.livePicture, 0, 0, 1, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeNameLabel, 1, 1, 1, 2, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeSlider, 1, 2, 1, 3, Qt.AlignCenter)
        self.mainLayout.addWidget(self.volumeLiveLabel, 1, 3, 1, 4, Qt.AlignCenter)
        self.mainLayout.addWidget(self.messageLabel, 2, 0, 1, 0, Qt.AlignCenter)
        self.mainLayout.addWidget(self.settingsBtn, 3, 1, Qt.AlignCenter)
        self.mainLayout.addWidget(self.startBtn, 3, 2, Qt.AlignCenter)
        self.mainLayout.addWidget(self.stopBtn, 3, 3, Qt.AlignCenter)
        self.mainLayout.addWidget(self.screenshotBtn, 3, 4, Qt.AlignCenter)
        self.mainLayout.addWidget(self.aiSupport, 3, 5, Qt.AlignCenter)

        #Finalizing the layout of the main screen
        self.setLayout(self.mainLayout)

        # Show black picture where the video should be
        blackImage = QImage()
        blackImage.load("Presets/Black.png")
        self.setImage(blackImage, manual=True)