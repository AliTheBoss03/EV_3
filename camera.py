import cv2
import requests

FLASK_SERVER_URL = "http://172.20.10.4:5000/process_image"

def capture_and_send_image():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        _, img_encoded = cv2.imencode('.jpg', frame)
        response = requests.post(
            FLASK_SERVER_URL,
            files={"image": img_encoded.tobytes()}
        )

        print(f"Sent image, received response: {response.status_code}")
        try:
            print(response.json())
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    capture_and_send_image()
