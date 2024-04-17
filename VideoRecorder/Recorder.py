import os
import cv2
import pyaudio
import wave
import numpy
from moviepy.editor import VideoFileClip, AudioFileClip
from datetime import datetime

class Recorder:
    def __init__(self, videoSize, settings):
        #Setting up the variable for the visual recording of the video
        self.videoSize = videoSize
        self.captureDevice = None
        self.settings = settings
        self.videoWriter = None
        self.videoFileName = ""
        #Variable to store the last calculated frame, so taking a screenshot can have it's own function
        self.lastVideoFrame = None

        #Setting up the variables for the voice recording
        self.audioFrameRate = 30000
        self.audioNumberOfChannels = 1
        self.audioVolumeLevel = 1.0
        self.audioCaptureDevice = None
        self.audioStream = None
        self.audioFrames = []

    def startRecorder(self):
        #Creating the capturing device for the visual part of the video
        self.captureDevice = cv2.VideoCapture(self.settings["cameraChoice"])

        #Creating the visual writer for the video with the name plus the current date
        currentTime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        self.videoFileName = self.settings["savePath"] + "/Recording-" + currentTime + ".mp4"
        codec = cv2.VideoWriter_fourcc(*"mp4v")
        self.videoWriter = cv2.VideoWriter(self.settings["savePath"] + "/TempRecording.mp4", codec, self.captureDevice.get(cv2.CAP_PROP_FPS), (int(self.captureDevice.get(3)),int(self.captureDevice.get(4))))

        #Creating the audio recorder device
        self.audioFrameRate = int(self.captureDevice.get(cv2.CAP_PROP_FPS))*1000
        self.audioCaptureDevice = pyaudio.PyAudio()
        self.audioStream = self.audioCaptureDevice.open(format=pyaudio.paInt16, channels=self.audioNumberOfChannels, rate=self.audioFrameRate, input=True, frames_per_buffer=1024, input_device_index=self.settings["audioChoice"])

    def getCurrentFrame(self):
        #Checking if the recording has been started, if not return None, meanin the recording is not running
        if self.captureDevice is None:
            return None
        
        #Getting the video and audio frames and checking if they have been correctly returned
        ret, frame = self.captureDevice.read()
        if self.audioCaptureDevice is None or self.audioStream is None:
            return None
        audioData = self.audioStream.read(1024)

        if not ret or audioData is None:
            return None
        
        #If the frame was succesfully retrieved, save for the screenshot functionality
        self.lastVideoFrame = frame

        #Store the volume controlled data in the audio buffer
        chunk = numpy.fromstring(audioData, numpy.int16)
        chunk = chunk * self.audioVolumeLevel
        audioData = chunk.astype(numpy.int16)
        self.audioFrames.append(audioData)

        #Write the video frame to the visual part of the video
        self.videoWriter.write(frame)

        #Return the current frame
        return frame
    
    def setAudioVolumeLevel(self, audioLevel):
        #The function is given an audioLevel parameter, float between 0 and 1.0 and sets it as the volume level
        self.audioVolumeLevel = audioLevel
    
    def getCurrentFrameTracked(self):
        #TODO: Implement the tracking and incorporate it
        ret, frame = self.captureDevice.read()
        if not ret:
            return None
        self.videoWriter.write(frame)
        return frame
    
    def stopRecorder(self):
        #Releasing the visual recorder parts of the video
        self.captureDevice.release()
        self.captureDevice = None
        self.videoWriter.release()
        self.videoWriter = None

        #Delete the last frame for the screenshot
        self.lastVideoFrame = None

        #Saving to an audio file the frames which were accumulated
        self.saveAudio()
        self.audioFrames = []

        #Releasing the audio recorder parts of the video
        self.audioStream.stop_stream()
        self.audioStream.close()
        self.audioStream = None
        self.audioCaptureDevice.terminate()
        self.audioCaptureDevice = None
        
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
        cv2.imwrite(screenshotPath, self.lastVideoFrame)
