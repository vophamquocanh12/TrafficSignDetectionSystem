from flask import Blueprint, Response, jsonify
import time

from services.camera_service import (
    start_camera_thread,
    stop_camera_service,
    get_latest_frame
)

from services.model_service import (
    detect_frame,
    encode_jpg
)

camera_bp = Blueprint("camera", __name__)


@camera_bp.route("/camera_raw")
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

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@camera_bp.route("/camera_detect")
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

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@camera_bp.route("/stop_camera", methods=["POST"])
def stop_camera():
    stop_camera_service()

    return jsonify({
        "message": "Camera đã ngắt"
    })