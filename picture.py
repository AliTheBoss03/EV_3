from ultralytics import YOLO

# Load the YOLO model
model = YOLO("/Users/alimo/Desktop/EV_3/AssetsBest/best.pt")


# Export the model
model.export(format='openvino', imgsz=640)