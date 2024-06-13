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
        # Tjek om der er en fil med navnet 'image' i POST-anmodningen
        if 'image' not in request.files:
            return jsonify({"error": "No image file found in the request"}), 400

        # Hent billede fra POST-anmodningen
        image = request.files['image'].read()
        image = Image.open(io.BytesIO(image))

        # Gem billedet midlertidigt (kan slettes senere)
        image_path = "/Users/amaan/Desktop/bil/event.jpg"  # Erstatt med stien hvor billedet skal gemmes
        
        image.save(image_path)

        # Send billede til EV3-serveren
        files = {"image": open(image_path, 'rb')}
        ev3_response = requests.post(EV3_SERVER_URL, files=files)

        if ev3_response.status_code != 200:
            print(f"Error from EV3 Server: {ev3_response.text}")
            return jsonify({"error": "Failed to send image to EV3"}), 500

        return jsonify({"status": "success", "message": "Image processed and sent to EV3"})

    except Exception as e:
        print(f"An error occurred in process_image: {e}")
        return jsonify({"error": f"An error occurred while processing the image: {e}"}), 500
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
