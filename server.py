from flask import Flask, request, jsonify
from PIL import Image
import io
import requests
import os

app = Flask(__name__)

# URL til EV3-serveren
EV3_SERVER_URL = "http://172.20.10.5:5000/command"  # Erstatt med din EV3-server URL

@app.route('/detect', methods=['GET'])
def detect():
    return jsonify({"status": "success", "predictions": []})

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        # Tjek om der er filer med navnet 'image' i POST-anmodningen
        if 'image' not in request.files:
            return jsonify({"error": "No image files found in the request"}), 400

        # Hent listen af billeder fra POST-anmodningen
        image_files = request.files.getlist('image')

        # Liste til at gemme detections fra hvert billede
        all_detections = []

        # Iterér over hvert billede i listen
        for image_file in image_files:
            # Hent billedet fra POST-anmodningen
            image = image_file.read()
            image = Image.open(io.BytesIO(image))

            # Gem billedet midlertidigt (kan slettes senere)
            image_path = f"/Users/amaan/Desktop/bil/{image_file.filename}"
            image.save(image_path)

            # Send billede til EV3-serveren
            files = {"image": open(image_path, 'rb')}
            ev3_response = requests.post(EV3_SERVER_URL, files=files)

            if ev3_response.status_code != 200:
                print(f"Error from EV3 Server: {ev3_response.text}")
                all_detections.append({"filename": image_file.filename, "error": "Failed to send image to EV3"})
            else:
                all_detections.append({"filename": image_file.filename, "status": "success", "message": "Image processed and sent to EV3"})

            # Slet det midlertidige billede
            os.remove(image_path)

        return jsonify({"status": "success", "detections": all_detections})

    except Exception as e:
        print(f"An error occurred in process_image: {e}")
        return jsonify({"error": f"An error occurred while processing the images: {e}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
