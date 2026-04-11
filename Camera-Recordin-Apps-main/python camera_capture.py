import cv2

def main():
    # Open the default camera (0)
    cam = cv2.VideoCapture(0)

    if not cam.isOpened():
        print("Could not open camera")
        return

    print("Press SPACE to capture image, ESC to exit.")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow("Camera", frame)

        key = cv2.waitKey(1)

        # SPACE key to capture image
        if key == 32:  # space key
            cv2.imwrite("captured_image.jpg", frame)
            print("Image captured and saved as captured_image.jpg")

        # ESC key to exit
        elif key == 27:
            print("Exiting...")
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()