from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import cv2
# from keras.models import load_model
# from keras.applications.mobilenet_v2 import preprocess_input
# import numpy as np

class UIRecorder(QThread):
    #Setting up the signal so this class can communicate with the MainPage
    changePixmap = pyqtSignal(QImage)
    soundChangeSignal = pyqtSignal(int)
    errorSignal = pyqtSignal(int)
    stopped = False
    startError = False
    errorValue = 0

    def __init__(self, settings, recorder):
        super().__init__()
        self.settings = settings
        self.recorder = recorder
        self.aiSupport = False
        returnValue = self.recorder.startRecorder()
        if returnValue != 0:
            self.stopped = True
            self.errorValue = returnValue
            self.startError = True

    def switchAISupport(self, isChecked):
        #Function for MainPage UIRecorder communication
        self.aiSupport = isChecked
        
    def run(self):
        #Check if ther was an error
        if self.startError:
            self.errorSignal.emit(self.errorValue)
            
        #Getting the current frame from the recorder
        while not self.stopped:
            frame, command = self.recorder.getCurrentFrame(self.aiSupport)
            #Handle the returned command, mainly the ones which change the sound volume
            self.handleCommand(command)

            if frame is not None:
                #Converting the image for the pyqt module
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgbImage.shape
                convertToQtFormat = QImage(rgbImage.data, w, h, QImage.Format_RGB888)

                #Send the image to the mainPage
                self.changePixmap.emit(convertToQtFormat)
        
    def handleCommand(self, command):
        #If there is no command return
        if command is None:
            return
    
        #Handle the volume commands: mute, voicedown, voiceup
        if command == "mute":
            self.soundChangeSignal.emit(0)
        elif command == "voicedown":
            self.soundChangeSignal.emit(-5)
        elif command == "voiceup":
            self.soundChangeSignal.emit(5)
        elif command == "ReadError":
            self.stopped = True
            self.errorValue = 4
            self.errorSignal.emit(self.errorValue)

    def stop(self):
        self.stopped = True
        if not self.startError:
            self.recorder.stopRecorder()
        self.quit()