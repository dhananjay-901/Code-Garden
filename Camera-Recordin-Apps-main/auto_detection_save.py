import cv2
import time
import os

os.makedirs("auto_faces", exist_ok=True)

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)
last_save = 0
cooldown = 2

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5)

    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    now = time.time()
    if len(faces) > 0 and now - last_save >= cooldown:
        for i, (x, y, w, h) in enumerate(faces):
            crop = frame[y:y+h, x:x+w]
            name = f"auto_faces/face_{int(now)}_{i}.jpg"
            cv2.imwrite(name, crop)
            print("Saved", name)
        last_save = now

    cv2.imshow("Auto Face Capture", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()
