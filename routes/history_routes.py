from flask import Blueprint, jsonify

from services.history_service import (
    get_history,
    get_chart_data,
    reset_history
)

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history():
    return jsonify(get_history())


@history_bp.route("/chart_data")
def chart_data():
    return jsonify(get_chart_data())


@history_bp.route("/reset", methods=["POST"])
def reset():
    return jsonify(reset_history())