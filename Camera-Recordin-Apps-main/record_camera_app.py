import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import time

class TkCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tkinter Camera Recorder")

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Cannot open camera")

        self.recording = False
        self.video_writer = None

        self.label = ttk.Label(root)
        self.label.pack()

        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Capture", command=self.capture).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Record", command=self.toggle_record).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Exit", command=self.exit).grid(row=0, column=2, padx=5)

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            if self.recording and self.video_writer:
                self.video_writer.write(frame)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(rgb))
            self.label.img = img
            self.label.configure(image=img)

        self.root.after(10, self.update_frame)

    def capture(self):
        ret, frame = self.cap.read()
        if ret:
            name = f"tk_capture_{int(time.time())}.jpg"
            cv2.imwrite(name, frame)
            print("Saved", name)

    def toggle_record(self):
        if not self.recording:
            w = int(self.cap.get(3))
            h = int(self.cap.get(4))
            name = f"tk_record_{int(time.time())}.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(name, fourcc, 20.0, (w, h))
            self.recording = True
            print("Recording started →", name)
        else:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
            print("Recording stopped")

    def exit(self):
        if self.video_writer:
            self.video_writer.release()
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    TkCameraApp(root)
    root.mainloop()
