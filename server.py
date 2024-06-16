from flask import Flask, request, jsonify
from PIL import Image
import io
import requests
import os

app = Flask(__name__)

# URL til EV3-serveren
EV3_SERVER_URL = "http://172.20.10.10:5000/command"  # Korrekt IP-adresse til din EV3-server

@app.route('/detect', methods=['GET'])
def detect():
    # Dette endpoint bruges til at tjekke kommunikation
    return jsonify({"status": "success", "predictions": []})

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file found in the request"}), 400

        image = request.files['image'].read()
        image = Image.open(io.BytesIO(image))

        # Gem billedet midlertidigt
        image_path = "C:/Users/amaan/desktop/bil/test_image.jpg"  # Sørg for, at denne sti er korrekt og findes
        image.save(image_path)

        # Send billede til EV3-serveren
        files = {"image": open(image_path, 'rb')}
        ev3_response = requests.post(EV3_SERVER_URL, files=files)

        if ev3_response.status_code != 200:
            error_message = "Error from EV3 Server: {ev3_response.text}"
            print(error_message)
            return jsonify({"error": "Failed to send image to EV3", "details": error_message}), 500

        return jsonify({"status": "success", "message": "Image processed and sent to EV3"})

    except Exception as e:
        error_message = f"An error occurred while processing the image: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
