import cv2
import requests

FLASK_SERVER_URL = "http://172.20.10.4:5000/process_image"  # Korrekt IP-adresse til din Flask-server

def capture_and_send_image():
    cap = cv2.VideoCapture(0)  # Vælg den korrekte kameraenhed
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        _, img_encoded = cv2.imencode('.jpg', frame)  # Gem som JPEG-fil
        response = requests.post(
            FLASK_SERVER_URL,
            files={"image": img_encoded.tobytes()}
        )

        print("Sent image, received response: {response.status_code}")
        try:
            print(response.json())
        except Exception as e:
            print("Request failed: {e}")

if __name__ == "__main__":
    capture_and_send_image()
