import sys
import cv2
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

class QtCamera(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Camera App")

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Camera not available")

        self.recording = False
        self.writer = None

        self.video_label = QLabel()
        self.video_label.setFixedSize(640, 480)

        self.capture_btn = QPushButton("Capture")
        self.capture_btn.clicked.connect(self.capture)

        self.record_btn = QPushButton("Record")
        self.record_btn.clicked.connect(self.toggle_record)

        layout = QVBoxLayout()
        layout.addWidget(self.video_label)

        controls = QHBoxLayout()
        controls.addWidget(self.capture_btn)
        controls.addWidget(self.record_btn)
        layout.addLayout(controls)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        if self.recording and self.writer:
            self.writer.write(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def capture(self):
        ret, frame = self.cap.read()
        if ret:
            name, _ = QFileDialog.getSaveFileName(self, "Save Image", "capture.jpg", "Images (*.jpg *.png)")
            if name:
                cv2.imwrite(name, frame)

    def toggle_record(self):
        if not self.recording:
            name, _ = QFileDialog.getSaveFileName(self, "Save Video", "video.avi", "Videos (*.avi)")
            if not name:
                return

            w = int(self.cap.get(3))
            h = int(self.cap.get(4))
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.writer = cv2.VideoWriter(name, fourcc, 20.0, (w, h))
            self.recording = True
            self.record_btn.setText("Stop")
        else:
            self.recording = False
            if self.writer:
                self.writer.release()
            self.record_btn.setText("Record")

    def closeEvent(self, event):
        if self.writer:
            self.writer.release()
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = QtCamera()
    win.show()
    sys.exit(app.exec_())
