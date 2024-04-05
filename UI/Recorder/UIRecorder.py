import cv2
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

class UIRecorder(QThread):
    changePixmap = pyqtSignal(QImage)
    stopped = False

    def __init__(self, settings, recorder):
        super().__init__()
        self.settings = settings
        self.recorder = recorder
        self.recorder.startRecorder()

    def run(self):
        while not self.stopped:
            frame = self.recorder.getCurrentFrame()
            if frame is not None:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgbImage.shape
                convertToQtFormat = QImage(rgbImage.data, w, h, QImage.Format_RGB888)
                self.changePixmap.emit(convertToQtFormat)
        
    def stop(self):
        self.stopped = True
        self.recorder.stopRecorder()
        self.quit()