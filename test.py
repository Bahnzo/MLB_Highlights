import sys
import os
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *

class VideoWidget(QWidget):

     def __init__(self, parent=None):
         super(VideoWidget, self).__init__(parent)

         self.setAutoFillBackground(False)
         self.setAttribute(Qt.WA_NoSystemBackground, True)
         self.setAttribute(Qt.WA_PaintOnScreen, True)
         palette = self.palette()
         palette.setColor(QPalette.Background, Qt.black)
         self.setPalette(palette)
         self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
         self.surface = VideoWidgetSurface(self)

     def videoSurface(self):
         return self.surface

     def closeEvent(self, event):
         del self.surface

     def sizeHint(self):
         return self.surface.surfaceFormat().sizeHint()

     def paintEvent(self, event):
         painter = QPainter(self)
         if (self.surface.isActive()):
             videoRect = self.surface.videoRect()
             if not videoRect.contains(event.rect()):
                 region = event.region()
                 region.subtract(videoRect)
                 brush = self.palette().background()
                 for rect in region.rects():
                     painter.fillRect(rect, brush)
             self.surface.paint(painter)
         else:
             painter.fillRect(event.rect(), self.palette().window())

     def resizeEvent(self, event):
         QWidget.resizeEvent(self, event)
         self.surface.updateVideoRect()

class VideoPlayer(QWidget):
     def __init__(self, parent=None):
         super(VideoPlayer, self).__init__(parent)

         self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)
         self.videoWidget = VideoWidget()
         self.openButton = QPushButton("Open...")
         self.openButton.clicked.connect(self.openFile)
         self.playButton = QPushButton()
         self.playButton.setEnabled(False)
         self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
         self.playButton.clicked.connect(self.play)

         self.positionSlider = QSlider(Qt.Horizontal)
         self.positionSlider.setRange(0, 0)
         self.positionSlider.sliderMoved.connect(self.setPosition)
         self.controlLayout = QHBoxLayout()
         self.controlLayout.setContentsMargins(0, 0, 0, 0)
         self.controlLayout.addWidget(self.openButton)
         self.controlLayout.addWidget(self.playButton)
         self.controlLayout.addWidget(self.positionSlider)
         layout = QVBoxLayout()
         layout.addWidget(self.videoWidget)
         layout.addLayout(self.controlLayout)

         self.setLayout(layout)

         self.mediaPlayer.setVideoOutput(self.videoWidget.videoSurface())
         self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
         self.mediaPlayer.positionChanged.connect(self.positionChanged)
         self.mediaPlayer.durationChanged.connect(self.durationChanged)

     def openFile(self):
         file_name = QFileDialog.getOpenFileName(self, "Open Movie", QDir.homePath())[0]
         if os.path.exists(file_name):
             self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(file_name)))
             self.playButton.setEnabled(True)

     def play(self):
         if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
             self.mediaPlayer.pause()
         else:
             self.mediaPlayer.play()

     def mediaStateChanged(self, state):
         if state == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
         else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

     def positionChanged(self, position):
         self.positionSlider.setValue(position)

     def durationChanged(self, duration):
         self.positionSlider.setRange(0, duration)

     def setPosition(self, position):
         self.mediaPlayer.setPosition(position)


if __name__ == '__main__':
     app = QApplication(sys.argv)

     player = VideoPlayer()
     player.show()

     sys.exit(app.exec_())