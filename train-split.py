from flask import Flask, render_template, request, jsonify, Response, send_file
from ultralytics import YOLO
from collections import defaultdict
import cv2
import os
import time
import threading

app = Flask(__name__)

MODEL_PATH = "runs/detect/traffic_sign_warning_model-2/weights/best.pt"
model = YOLO(MODEL_PATH)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CLASS_NAMES = {
    0: "DuongNguoiDiBoCatNgang",
    1: "TreEm",
    2: "CongTruong",
    3: "GiaoNhauVoiDuongUuTien",
    4: "GiaoNhauCoTinHieuDen",
    5: "DuongGiaoNhau"
}

history_scan = defaultdict(int)
latest_output = None

camera = None
latest_frame = None
camera_lock = threading.Lock()
camera_running = False


def start_camera_thread():
    global camera, latest_frame, camera_running

    if camera_running:
        return

    camera_running = True
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def update():
        global latest_frame

        while camera_running:
            success, frame = camera.read()
            if success:
                with camera_lock:
                    latest_frame = frame.copy()

    thread = threading.Thread(target=update, daemon=True)
    thread.start()


def get_latest_frame():
    with camera_lock:
        if latest_frame is None:
            return None
        return latest_frame.copy()


def detect_frame(frame):
    results = model.predict(frame, conf=0.5, verbose=False)
    annotated = results[0].plot()

    if results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES.get(class_id, "Unknown")
            history_scan[class_name] += 1

    return annotated


def encode_jpg(frame):
    ret, buffer = cv2.imencode(".jpg", frame)
    if not ret:
        return None
    return buffer.tobytes()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/camera_raw")
def camera_raw():
    start_camera_thread()

    def generate():
        while True:
            frame = get_latest_frame()
            if frame is None:
                time.sleep(0.03)
                continue

            frame_bytes = encode_jpg(frame)
            if frame_bytes is None:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/camera_detect")
def camera_detect():
    start_camera_thread()

    def generate():
        while True:
            frame = get_latest_frame()
            if frame is None:
                time.sleep(0.03)
                continue

            output = detect_frame(frame)
            frame_bytes = encode_jpg(output)

            if frame_bytes is None:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.route("/upload_image", methods=["POST"])
def upload_image():
    global latest_output

    file = request.files["image"]
    timestamp = int(time.time())

    input_path = os.path.join(UPLOAD_FOLDER, f"input_{timestamp}.jpg")
    output_path = os.path.join(OUTPUT_FOLDER, f"output_{timestamp}.jpg")

    file.save(input_path)

    frame = cv2.imread(input_path)
    output = detect_frame(frame)

    cv2.imwrite(output_path, output)
    latest_output = output_path

    return jsonify({
        "input": "/" + input_path.replace("\\", "/"),
        "output": "/" + output_path.replace("\\", "/")
    })


@app.route("/upload_video", methods=["POST"])
def upload_video():
    global latest_output

    file = request.files["video"]
    timestamp = int(time.time())

    input_path = os.path.join(UPLOAD_FOLDER, f"input_{timestamp}.mp4")
    output_path = os.path.join(OUTPUT_FOLDER, f"output_{timestamp}.mp4")

    file.save(input_path)

    cap = cv2.VideoCapture(input_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps == 0:
        fps = 25

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height)
    )

    while True:
        success, frame = cap.read()
        if not success:
            break

        output = detect_frame(frame)
        writer.write(output)

    cap.release()
    writer.release()

    latest_output = output_path

    return jsonify({
        "input": "/" + input_path.replace("\\", "/"),
        "output": "/" + output_path.replace("\\", "/")
    })


@app.route("/history")
def history():
    return jsonify(dict(history_scan))


@app.route("/reset", methods=["POST"])
def reset():
    history_scan.clear()
    return jsonify({"message": "Đã reset lịch sử"})


@app.route("/download")
def download():
    if latest_output and os.path.exists(latest_output):
        return send_file(latest_output, as_attachment=True)

    return jsonify({"error": "Chưa có file output"}), 404


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )