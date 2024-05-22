import os
import cv2
import pyaudio
import wave
import numpy
import tensorflow as tf
import time
from moviepy.editor import VideoFileClip, AudioFileClip
from datetime import datetime

class Recorder:
    def __init__(self, settings):
        #Setting up the variable for the visual recording of the video
        self.videoFrameRate = 30
        self.videoSize = None
        self.captureDevice = None
        self.settings = settings
        self.videoWriter = None
        self.videoFileName = ""
        self.fpsTimeRemainder = 0
        self.frameRepeatedCounter = 0
        #Variable to store the last calculated frame, so taking a screenshot can have it's own function
        self.lastVideoFrame = None

        #Setting up the variables for the voice recording
        self.audioFrameRate = 30000
        self.audioNumberOfChannels = 1
        self.audioVolumeLevel = 1.0
        self.audioCaptureDevice = None
        self.audioStream = None
        self.audioFrames = []
        self.audioError = False

        #Loading in the MobileNet model and variables for using it
        self.model = tf.saved_model.load("handGestModel\saved_model")
        self.drawPixel = []
        self.lineTickness = 2
        self.drawNewLine = True
        self.lastDrawAppend = time.time()
        self.frameTimeMax = 1
        self.frameTimer = self.frameTimeMax
        self.predictTreshold = 0.95
        self.currentPrediction = None
        self.predictConfidenceCounterMax = 2
        self.predictConfidenceCounter = self.predictConfidenceCounterMax
        self.predictFrameWaitCounterMax = 60
        self.predictFrameWaitCounter = self.predictFrameWaitCounterMax
        self.classes = [{'id':1, 'name':"draw"},{'id':2, 'name':"clear"},{'id':3, 'name':"mute"},{'id':4, 'name':"voicedown"},{'id':5, 'name':"voiceup"}]

    def setSettings(self, settings):
        #Utility function to change the settings of the object
        self.settings = settings

    def startRecorder(self):
        #Creating the capturing device for the visual part of the video
        try:
            self.captureDevice = cv2.VideoCapture(self.settings["cameraChoice"])
        except Exception:
            self.captureDevice = None
            return 1
        self.videoFrameRate = self.captureDevice.get(cv2.CAP_PROP_FPS)

        #Creating the visual writer for the video with the name plus the current date
        currentTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.videoFileName = self.settings["savePath"] + "/Recording-" + currentTime + ".mp4"
        codec = cv2.VideoWriter_fourcc(*"mp4v")
        try:
            self.videoWriter = cv2.VideoWriter(self.settings["savePath"] + "/TempRecording.mp4", 
                                            codec, self.captureDevice.get(cv2.CAP_PROP_FPS), 
                                            (int(self.captureDevice.get(3)),
                                                int(self.captureDevice.get(4))))
        except Exception:
            self.captureDevice = None
            self.videoWriter = None
            return 2
        self.videoSize = (int(self.captureDevice.get(3)), int(self.captureDevice.get(4)))
        
        #Creating the audio recorder device
        self.audioFrameRate = int(self.captureDevice.get(cv2.CAP_PROP_FPS))*1024
        try:
            self.audioCaptureDevice = pyaudio.PyAudio()
            self.audioStream = self.audioCaptureDevice.open(format=pyaudio.paInt16, 
                                                            channels=self.audioNumberOfChannels, 
                                                            rate=self.audioFrameRate, input=True, 
                                                            frames_per_buffer=1024, 
                                                            input_device_index=self.settings["audioChoice"])
        except Exception:
            self.captureDevice = None
            self.videoWriter = None
            self.audioCaptureDevice = None
            self.audioStream = None
            return 3
        return 0

    def getCurrentFrame(self, useAI=False):
        #Checking if the recording has been started, if not return None, meanin the recording is not running
        if self.captureDevice is None:
            return None, None
        command = None
        boundingBox = None
        startTime = time.time()

        #Getting the video and audio frames and checking if they have been correctly returned
        try:
            ret, frame = self.captureDevice.read()
            if self.audioCaptureDevice is None or self.audioStream is None:
                return None, None
            audioData = self.audioStream.read(1024)
        except OSError:
            self.audioError = True
            return None, "ReadError"
        self.frameTimer -= 1
        self.predictFrameWaitCounter -= 1
        if not ret or audioData is None:
            return None, None
        
        #If the usage of AI is needed process the image
        if useAI and self.frameTimer <= 0:
            command, boundingBox = self.processFrame(frame)
            self.frameTimer = self.frameTimeMax
            #Check if new prediction should be processed or not
            if self.predictFrameWaitCounter > 0:
                command = None

        #If there was a prediction handle it, after a couple of frames from the last detection
        if command is not None:
            #In order to bypass accidental detections, a number of detections are needed from the same hand gesture
            if self.currentPrediction == command:
                self.predictConfidenceCounter -= 1
            else:
                self.currentPrediction = command
                self.predictConfidenceCounter = self.predictConfidenceCounterMax - 1

            if self.predictConfidenceCounter <= 0:
                self.processDrawCommands(command, boundingBox)
                if command != "draw":
                    self.predictFrameWaitCounter = self.predictFrameWaitCounterMax
                    self.currentPrediction = None
        
        #Draw the line to the screen
        frame = self.drawLines(frame)

        #Flip the screen horizontally
        frame = cv2.flip(frame, 1)

        #If the frame was succesfully retrieved, save for the screenshot functionality
        self.lastVideoFrame = frame

        #Store the volume controlled data in the audio buffer
        chunk = numpy.fromstring(audioData, numpy.int16)
        chunk = chunk * self.audioVolumeLevel
        audioData = chunk.astype(numpy.int16)
        self.audioFrames.append(audioData)

        #Write the video frame to the visual part of the video
        if self.videoWriter is None:
            return None, None
        self.videoWriter.write(frame)

        #FPS handling, if the fps is too low, the video should not be sped up
        self.fpsTimeRemainder += max(time.time() - startTime - 1./self.videoFrameRate,0)
        try:
            self.dynamicFPSHandler(frame)
        except OSError:
            return None, "ReadError"

        #Return the current frame
        return frame, command
    
    def drawLines(self, frame):
        #Draw lines to the screen
        for i in range(1, len(self.drawPixel)):
            #Check whether the next pair would be the same, if yes it's a new line
            if i < len(self.drawPixel) - 1 and self.drawPixel[i] == self.drawPixel[i+1]:
                continue
            cv2.line(frame, self.drawPixel[i-1], self.drawPixel[i], (255, 255, 255), thickness=self.lineTickness)

        return frame
    
    def processDrawCommands(self, command, boundingBox):
        #Check whether the last draw event was 2 seconds before, if yes, start a new line
        if time.time() - self.lastDrawAppend > 2:
            self.drawNewLine = True

        #Process the commands
        if command == "draw":
            self.drawPixel.append((int((boundingBox[1] + boundingBox[3])/2), int(boundingBox[0])))
            self.lastDrawAppend = time.time()
            #In order to start drawing a new line, we double the first point
            if self.drawNewLine:
                self.drawPixel.append((int((boundingBox[1] + boundingBox[3])/2), int(boundingBox[0])))
                self.drawNewLine = False
        elif command == "clear":
            print(self.drawPixel)
            self.drawPixel = []
    
    def dynamicFPSHandler(self, frame):
        #This function is responsible for keeping track of the fps of the video, with the help of the time values from the getCurrentFrame function
        while self.fpsTimeRemainder >= 1./self.videoFrameRate:
            self.videoWriter.write(frame)
            self.fpsTimeRemainder -= 1./self.videoFrameRate
            audioData = self.audioStream.read(1024)
            chunk = numpy.fromstring(audioData, numpy.int16)
            chunk = chunk * self.audioVolumeLevel
            audioData = chunk.astype(numpy.int16)
            self.audioFrames.append(audioData)
            self.frameRepeatedCounter +=1

        #Dinamicly dial down the rate at which the AI model processes images in case of too much delay
        if self.frameRepeatedCounter > 10:
            self.frameRepeatedCounter = 0
            if self.frameTimeMax < 5:
                self.frameTimeMax +=1
    
    def setAudioVolumeLevel(self, audioLevel):
        #The function is given an audioLevel parameter, float between 0 and 1.0 and sets it as the volume level
        self.audioVolumeLevel = audioLevel
    
    def processFrame(self, frame):
        #Adding batch layer and resize image
        inputArray = numpy.expand_dims(frame, 0)

        #Running the detection
        detections = self.model(inputArray)

        # Formatting the detection
        detectionBoxes = detections['detection_boxes'][0].numpy()
        detectionClasses = detections['detection_classes'][0].numpy().astype(numpy.int32)
        detectionScores = detections['detection_scores'][0].numpy()
        returnClass = None
        boundingBox = None

        #Looping through the detections
        for i in range(len(detectionBoxes)):
            if detectionScores[i] >= self.predictTreshold:
                #Get the name of the predicted class
                for c in self.classes:
                    if c['id'] == detectionClasses[i]:
                        returnClass = c['name']
                        break
                yMin = int(detectionBoxes[i][0] * self.videoSize[1])
                xMin = int(detectionBoxes[i][1] * self.videoSize[0])
                yMax = int(detectionBoxes[i][2] * self.videoSize[1])
                xMax = int(detectionBoxes[i][3] * self.videoSize[0])
                boundingBox = [yMin, xMin, yMax, xMax]
        return returnClass, boundingBox

    def stopRecorder(self):
        #Releasing the visual recorder parts of the video
        self.captureDevice.release()
        self.captureDevice = None
        self.videoWriter.release()
        self.videoWriter = None
        self.fpsTimeRemainder = 0
        self.frameTimer = self.frameTimeMax
        self.drawPixel = []
        self.predictFrameWaitCounter = self.predictFrameWaitCounterMax
        self.currentPrediction = None
        self.predictConfidenceCounter = self.predictConfidenceCounterMax
    
        #Delete the last frame for the screenshot
        self.lastVideoFrame = None

        #Saving to an audio file the frames which were accumulated
        self.saveAudio()
        self.audioFrames = []

        #Releasing the audio recorder parts of the video
        if not self.audioError:
            self.audioStream.stop_stream()
        self.audioStream.close()
        self.audioStream = None
        self.audioCaptureDevice.terminate()
        self.audioCaptureDevice = None
        self.audioError = False

        
        #Merging the video and audio file to a single mp4
        self.mergeAudioVideo()

        #Deleting the temp audio and video files
        os.remove(self.settings["savePath"] + "/TempAudio.wav")
        os.remove(self.settings["savePath"] + "/TempRecording.mp4")


    def saveAudio(self):
        #Creating an audio file from the gotten audio input
        wf = wave.open(self.settings["savePath"] + "/TempAudio.wav", 'wb')
        wf.setnchannels(self.audioNumberOfChannels)
        wf.setsampwidth(self.audioCaptureDevice.get_sample_size(pyaudio.paInt16))
        wf.setframerate(self.audioFrameRate)
        wf.writeframes(b''.join(self.audioFrames))
        wf.close()

    def mergeAudioVideo(self):
        #Create the paths of the audio and video files
        audioPath = self.settings["savePath"] + "/TempAudio.wav"
        videoPath = self.settings["savePath"] + "/TempRecording.mp4"

        #Create instances of VideoFileClip and AudioFileClip
        videoEditor = VideoFileClip(videoPath)
        audioEditor = AudioFileClip(audioPath)

        #Merge the audio and video clips
        fullVideo = videoEditor.set_audio(audioEditor)

        #Write the merged video file to the saved file
        fullVideo.write_videofile(self.videoFileName)

    def takeScreenshot(self):
        #Check if there is a last frame stored, meaning a video is running
        if self.lastVideoFrame is None:
            return None
        
        #Get name combined with current time, to avoid conflicts
        currentTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        screenshotPath = self.settings["screenshotPath"] + "/Screenshot-" + currentTime + ".jpg"
        try:
            cv2.imwrite(screenshotPath, self.lastVideoFrame)
        except Exception:
            return None