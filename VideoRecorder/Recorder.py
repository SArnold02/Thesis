import cv2
from datetime import datetime

class Recorder:
    def __init__(self, videoSize, settings):
        self.videoSize = videoSize
        self.captureDevice = None
        self.settings = settings
        self.videoWriter = None

    def startRecorder(self):
        self.captureDevice = cv2.VideoCapture(self.settings["cameraChoice"])

        currentTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        fileName = self.settings["savePath"] + "/Recording-" + currentTime + ".mp4"
        codec = cv2.VideoWriter_fourcc(*"MP4V")
        self.videoWriter = cv2.VideoWriter(fileName, codec, self.captureDevice.get(cv2.CAP_PROP_FPS), (int(self.captureDevice.get(3)),int(self.captureDevice.get(4))))

    def getCurrentFrame(self):
        if self.captureDevice is None:
            return None

        ret, frame = self.captureDevice.read()
        if not ret:
            return None
        self.saveFrame(frame)
        return frame
    
    def getCurrentFrameTracked(self):
        #TODO: Implement the tracking and incorporate it
        ret, frame = self.captureDevice.read()
        if not ret:
            return None
        self.saveFrame(frame)
        return frame
    
    def saveFrame(self, frame):
        self.videoWriter.write(frame)

    def stopRecorder(self):
        self.captureDevice.release()
        self.captureDevice = None
        self.videoWriter.release()
        self.videoWriter = None