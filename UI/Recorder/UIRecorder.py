from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage

import cv2
# from keras.models import load_model
# from keras.applications.mobilenet_v2 import preprocess_input
# import numpy as np

class UIRecorder(QThread):
    changePixmap = pyqtSignal(QImage)
    stopped = False

    def __init__(self, settings, recorder):
        super().__init__()
        self.settings = settings
        self.recorder = recorder
        self.recorder.startRecorder()

        # self.model = load_model("./mobile.keras")

    # def preprocess_image(image):
    #     image = image.resize((224, 224))  # Resize to match MobileNetV2 input size
    #     image = np.array(image)  # Convert to numpy array
    #     image = tf.keras.applications.mobilenet_v2.preprocess_input(image)  # Normalize according to MobileNetV2
    #     image = np.expand_dims(image, axis=0)  # Add batch dimension
    #     return image

    # def predict(self, image):
        # image = preprocess_input(image)
        # self.model.predict(image)

    def run(self):
        while not self.stopped:
            frame = self.recorder.getCurrentFrame()
            if frame is not None:
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, _ = rgbImage.shape

                # predImage = cv2.resize(rgbImage, (224, 224))

                # # Step 3: Preprocess the image for prediction
                # predImage = np.expand_dims(predImage, axis=0)  # Add batch dimension
                # self.predict(predImage)

                convertToQtFormat = QImage(rgbImage.data, w, h, QImage.Format_RGB888)
                self.changePixmap.emit(convertToQtFormat)
        
    def stop(self):
        self.stopped = True
        self.recorder.stopRecorder()
        self.quit()