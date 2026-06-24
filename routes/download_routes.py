from flask import Blueprint, jsonify, send_file
from io import BytesIO
import os
import state

download_bp = Blueprint("download", __name__)


@download_bp.route("/download")
def download():
    print("latest_output_type:", state.latest_output_type)
    print("latest_video_input_path:", state.latest_video_input_path)

    if state.latest_output_type == "image":
        if state.latest_output_data is None:
            return jsonify({"error": "Chưa có ảnh output"}), 404

        return send_file(
            BytesIO(state.latest_output_data),
            mimetype="image/jpeg",
            as_attachment=True,
            download_name="output_detect_image.jpg"
        )

    if state.latest_output_type == "video":
        if not state.latest_video_input_path:
            return jsonify({"error": "Chưa có video input"}), 404

        if not os.path.exists(state.latest_video_input_path):
            return jsonify({"error": "Không tìm thấy video tạm"}), 404

        return send_file(
            state.latest_video_input_path,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="test_video_input.mp4"
        )

    return jsonify({"error": "Chưa có output để tải"}), 404