from ultralytics import YOLO

def main():
    model = YOLO("yolov8n.pt")

    model.train(
        data="data.yaml",
        epochs=50,
        imgsz=640,
        batch=8,
        name="traffic_sign_warning_model"
    )

if __name__ == "__main__":
    main()
