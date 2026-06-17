from flask import Flask, render_template, request, jsonify, Response, send_file
from ultralytics import YOLO
from collections import defaultdict
import cv2
import os
import time
import threading

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
last_detect_time = {}
DETECT_COOLDOWN = 3  # Giới hạn thời gian giữa các lần phát hiện cùng loại (giây)
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

@app.route("/video_raw_stream/<filename>")
def video_raw_stream(filename):
    video_path = os.path.join(UPLOAD_FOLDER, filename)

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

    input_path = os.path.join(UPLOAD_FOLDER, f"input_{timestamp}.mp4")
    file.save(input_path)

    filename = f"input_{timestamp}.mp4"
    video_pause[filename] = False

    return jsonify({
    "video_id": filename,
    "input": f"/video_raw_stream/{filename}",
    "output": f"/video_detect_stream/{filename}"
    })


@app.route("/video_detect_stream/<filename>")
def video_detect_stream(filename):
    video_path = os.path.join(UPLOAD_FOLDER, filename)

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
