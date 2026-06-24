from flask import Blueprint, request, jsonify, Response

import state
from services.image_service import process_image

image_bp = Blueprint("image", __name__)


@image_bp.route("/upload_image", methods=["POST"])
def upload_image():
    file = request.files["image"]

    success = process_image(file)

    if not success:
        return jsonify({"error": "Không xử lý được ảnh"}), 400

    return jsonify({
        "output": "/preview_output_image"
    })


@image_bp.route("/preview_output_image")
def preview_output_image():
    if state.latest_output_data is None:
        return "No image", 404

    return Response(
        state.latest_output_data,
        mimetype="image/jpeg"
    )