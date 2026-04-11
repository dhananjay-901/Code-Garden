import cv2
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class CameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Camera Capture")

        self.cam = cv2.VideoCapture(0)

        self.label = ttk.Label(root)
        self.label.pack()

        capture_btn = ttk.Button(root, text="Capture Image", command=self.capture)
        capture_btn.pack(pady=10)

        exit_btn = ttk.Button(root, text="Exit", command=self.close)
        exit_btn.pack(pady=10)

        self.update_frame()

    def update_frame(self):
        ret, frame = self.cam.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(Image.fromarray(frame))
            self.label.img = img
            self.label.config(image=img)

        self.root.after(10, self.update_frame)

    def capture(self):
        ret, frame = self.cam.read()
        if ret:
            cv2.imwrite("captured_gui.jpg", frame)
            print("Image saved as captured_gui.jpg")

    def close(self):
        self.cam.release()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    CameraApp(root)
    root.mainloop()