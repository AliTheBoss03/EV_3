from flask import Flask, request, jsonify
import requests
from PIL import Image
import io

app = Flask(__name__)

#model_path = '/path_to_your_model/model.h5'
#model = tf.keras.models.load_model(model_path)

ROBOFLOW_API_KEY = "qn06Xx676ZZRgpdMTVyB"  # Brug din egen Roboflow API-nøgle
ROBOFLOW_MODEL_ENDPOINT = "https://detect.roboflow.com/robot-ev3/4"  # URL til Roboflow-modellen
EV3_SERVER_URL = "http://172.20.10.5:5000/command"  # IP-adressen til EV3-serveren, opdater hvis nødvendigt

@app.route('/detect', methods=['GET'])
def detect():
    return jsonify({"status": "success", "predictions": []})

@app.route('/process_image', methods=['POST'])
def process_image():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file found in the request"}), 400

        image = request.files['image'].read()
        image = Image.open(io.BytesIO(image))

        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        response = requests.post(
            ROBOFLOW_MODEL_ENDPOINT,
            files={"file": img_byte_arr},
            headers={"Authorization": f"Bearer {ROBOFLOW_API_KEY}"}
        )

        if response.status_code != 200:
            print(f"Error from Roboflow: {response.text}")
            return jsonify({"error": "Failed to process image"}), 500

        detections = response.json()

        # Process detections and send commands to EV3
        send_commands_to_ev3(detections)
        
        return jsonify(detections)
    except Exception as e:
        print(f"An error occurred in process_image: {e}")
        return jsonify({"error": f"An error occurred while processing the image: {e}"}), 500

def send_commands_to_ev3(detections):
    for detection in detections['predictions']:
        label = detection['label']
        # Define commands based on detections
        if label == 'orange_ball':
            command = 'collect_orange_ball'
        elif label == 'white_ball':
            command = 'collect_white_ball'
        elif label in ['egg', 'cross', 'wall']:
            command = 'avoid_obstacle'
        elif label == 'goal':
            command = 'release_balls'
        else:
            command = 'unknown'
        
        try:
            response = requests.post(EV3_SERVER_URL, json={'command': command})
            if response.status_code != 200:
                print(f"Failed to send command to EV3: {response.text}")
        except Exception as e:
            print(f"An error occurred while sending command to EV3: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
