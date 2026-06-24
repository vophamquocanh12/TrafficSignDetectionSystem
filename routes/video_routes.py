from flask import Blueprint, request, jsonify, Response
import time
import os

import state
from services.video_service import (
    upload_and_start_video,
    pause_video,
    resume_video,
    stop_video
)
from services.model_service import encode_jpg

video_bp = Blueprint("video", __name__)


@video_bp.route("/upload_video", methods=["POST"])
def upload_video():
    if "video" not in request.files:
        return jsonify({"error": "Không có file video"}), 400

    file = request.files["video"]

    if file.filename == "":
        return jsonify({"error": "Chưa chọn video"}), 400

    session_id = upload_and_start_video(file)

    if not state.latest_video_input_path:
        return jsonify({"error": "Chưa lưu được đường dẫn video tạm"}), 500

    if not os.path.exists(state.latest_video_input_path):
        return jsonify({"error": "File video tạm không tồn tại"}), 500

    state.latest_output_type = "video"

    return jsonify({
        "video_id": str(session_id),
        "input": "/video_raw_stream?sid=" + str(session_id),
        "output": "/video_detect_stream?sid=" + str(session_id)
    })


@video_bp.route("/video_raw_stream")
def video_raw_stream():
    sid = request.args.get("sid")

    if not sid:
        return "Thiếu sid", 400

    def generate():
        while True:
            with state.current_video_lock:
                current_session = str(state.current_video.get("session"))

                if current_session != str(sid):
                    time.sleep(0.01)
                    continue

                frame = state.current_video.get("raw_frame")
                finished = state.current_video.get("finished")

            if frame is None:
                if finished:
                    break

                time.sleep(0.01)
                continue

            frame_bytes = encode_jpg(frame)

            if frame_bytes is None:
                time.sleep(0.01)
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


@video_bp.route("/video_detect_stream")
def video_detect_stream():
    sid = request.args.get("sid")

    if not sid:
        return "Thiếu sid", 400

    def generate():
        while True:
            with state.current_video_lock:
                current_session = str(state.current_video.get("session"))

                if current_session != str(sid):
                    time.sleep(0.01)
                    continue

                frame = state.current_video.get("detect_frame")
                finished = state.current_video.get("finished")

            if frame is None:
                if finished:
                    break

                time.sleep(0.01)
                continue

            frame_bytes = encode_jpg(frame)

            if frame_bytes is None:
                time.sleep(0.01)
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


@video_bp.route("/pause_video", methods=["POST"])
def pause_video_route():
    pause_video()

    return jsonify({
        "message": "Video đã tạm dừng"
    })


@video_bp.route("/resume_video", methods=["POST"])
def resume_video_route():
    resume_video()

    return jsonify({
        "message": "Video tiếp tục chạy"
    })


@video_bp.route("/stop_video", methods=["POST"])
def stop_video_route():
    stop_video()

    return jsonify({
        "message": "Đã xóa video"
    })