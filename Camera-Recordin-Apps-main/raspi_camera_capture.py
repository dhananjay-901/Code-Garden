import cv2

def main():
    print("Enter camera index (0, 1, 2...): ")
    cam_index = int(input("> "))

    cam = cv2.VideoCapture(cam_index)

    if not cam.isOpened():
        print("Could not open camera on index", cam_index)
        return

    print("Press SPACE to capture image, ESC to exit.")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break

        cv2.imshow(f"Camera {cam_index}", frame)
        key = cv2.waitKey(1)

        if key == 32:  # SPACE
            filename = f"raspi_capture_{cam_index}.jpg"
            cv2.imwrite(filename, frame)
            print(f"Image saved as {filename}")

        elif key == 27:  # ESC
            print("Exiting...")
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()