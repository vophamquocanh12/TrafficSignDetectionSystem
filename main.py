from flask import Flask, render_template, request, jsonify, Response, send_file
from ultralytics import YOLO
from collections import defaultdict
import cv2
import os
import time
import threading
import tempfile
import numpy as np
from io import BytesIO

app = Flask(__name__)

MODEL_PATH = "runs/detect/traffic_sign_warning_model/weights/best.pt"
model = YOLO(MODEL_PATH)

video_frames = {}
video_index = {}
video_lock = threading.Lock()
video_pause = {}
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

CLASS_NAMES = {
    0: "Đường người đi bộ cắt ngang",
    1: "Trẻ em",
    2: "Công trường",
    3: "Giao nhau với đường ưu tiên",
    4: "Giao nhau có tín hiệu đèn",
    5: "Đường giao nhau"
}

history_scan = defaultdict(int)
detection_timeline = []
last_detect_time = {}
DETECT_COOLDOWN = 3  # Giới hạn thời gian giữa các lần phát hiện cùng loại (giây)
latest_output = None

camera = None
latest_frame = None
camera_lock = threading.Lock()
camera_running = False

latest_output_data = None
latest_output_name = None
latest_output_type = None
latest_video_input_path = None
video_temp_paths = {}

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

@app.route("/stop_camera", methods=["POST"])
def stop_camera():

    global camera
    global camera_running
    global latest_frame
    global latest_detect_frame

    camera_running = False

    if camera:
        camera.release()
        camera = None

    latest_frame = None
    latest_detect_frame = None

    return jsonify({
        "message":"Camera đã ngắt"
    })

def get_latest_frame():
    with camera_lock:
        if latest_frame is None:
            return None
        return latest_frame.copy()


def detect_frame(frame):
    results = model.predict(frame, conf=0.45, imgsz=320, verbose=False)
    annotated = results[0].plot(
    conf=False,
    labels=True
)

    if results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES.get(class_id, "Unknown")
            current_time = time.time()
            if class_name not in last_detect_time:
                history_scan[class_name] += 1
                detection_timeline.append({
                "time": time.strftime("%H:%M:%S"),
                "class_name": class_name
                })
                last_detect_time[class_name] = current_time

            elif current_time - last_detect_time[class_name] > DETECT_COOLDOWN:
                history_scan[class_name] += 1
                last_detect_time[class_name] = current_time

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
    global latest_output_data, latest_output_name, latest_output_type

    file = request.files["image"]

    file_bytes = file.read()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    output = detect_frame(frame)

    success, buffer = cv2.imencode(".jpg", output)

    if not success:
        return jsonify({"error": "Không xử lý được ảnh"}), 400

    latest_output_data = buffer.tobytes()
    latest_output_name = "output_detect_image.jpg"
    latest_output_type = "image"

    input_base64 = "data:image/jpeg;base64,"
    output_path = "/preview_output_image"

    return jsonify({
        "output": output_path
    })

@app.route("/preview_output_image")
def preview_output_image():
    if latest_output_data is None:
        return "No image", 404

    return Response(
        latest_output_data,
        mimetype="image/jpeg"
    )

@app.route("/video_raw_stream/<filename>")
def video_raw_stream(filename):
    video_path = video_temp_paths.get(filename)

    if video_path is None:
        return "Không tìm thấy video tạm", 404

    def generate():
        cap = cv2.VideoCapture(video_path)

        while True:
            while video_pause.get(filename, False):
                time.sleep(0.1)
            success, frame = cap.read()
            
            if not success:
                break
            time.sleep(0.1)  # Giảm tốc độ stream để tránh quá tải
            frame_bytes = encode_jpg(frame)

            if frame_bytes is None:
                continue

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

        cap.release()

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/upload_video", methods=["POST"])
def upload_video():
    file = request.files["video"]
    timestamp = int(time.time())

    global latest_video_input_path, latest_output_type

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )

    file.save(temp_file.name)
    temp_file.close()

    input_path = temp_file.name

    latest_video_input_path = input_path
    latest_output_type = "video"

    filename = f"input_{timestamp}.mp4"
    video_pause[filename] = False
    video_temp_paths[filename] = input_path

    return jsonify({
    "video_id": filename,
    "input": f"/video_raw_stream/{filename}",
    "output": f"/video_detect_stream/{filename}"
    })


@app.route("/video_detect_stream/<filename>")
def video_detect_stream(filename):
    video_path = video_temp_paths.get(filename)

    if video_path is None:
        return "Không tìm thấy video tạm"

    def generate():
        cap = cv2.VideoCapture(video_path)

        while True:
            while video_pause.get(filename, False):
                time.sleep(0.1)
            success, frame = cap.read()

            if not success:
                break

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

        cap.release()

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/pause_video/<video_id>", methods=["POST"])
def pause_video(video_id):

    if video_id in video_pause:
        video_pause[video_id] = True

    return jsonify({
        "message": "Video đã tạm dừng"
    })

@app.route("/resume_video/<video_id>", methods=["POST"])
def resume_video(video_id):

    if video_id in video_pause:
        video_pause[video_id] = False

    return jsonify({
        "message": "Video tiếp tục"
    })

@app.route("/history")
def history():
    return jsonify(dict(history_scan))

@app.route("/chart_data")
def chart_data():
    return jsonify({
        "counts": dict(history_scan),
        "timeline": detection_timeline[-30:]
    })

@app.route("/reset", methods=["POST"])
def reset():
    history_scan.clear()
    last_detect_time.clear()
    detection_timeline.clear()

    return jsonify({
        "message": "Đã reset lịch sử"
    })



@app.route("/download")
def download():
    global latest_output_data
    global latest_output_name
    global latest_output_type
    global latest_video_input_path

    if latest_output_type == "image":
        if latest_output_data is None:
            return jsonify({"error": "Chưa có ảnh output"}), 404

        return send_file(
            BytesIO(latest_output_data),
            mimetype="image/jpeg",
            as_attachment=True,
            download_name="output_detect_image.jpg"
        )

    if latest_output_type == "video":
        if latest_video_input_path is None:
            return jsonify({"error": "Chưa có video output"}), 404

        temp_output = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".mp4"
        )

        output_path = temp_output.name
        temp_output.close()

        cap = cv2.VideoCapture(latest_video_input_path)

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 25

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

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

        return send_file(
            output_path,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="output_detect_video.mp4"
        )

    return jsonify({"error": "Chưa có output để tải"}), 404

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        use_reloader=False
    )
