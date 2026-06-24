from flask import Blueprint, jsonify

from services.sound_service import get_and_clear_sound_events

sound_bp = Blueprint("sound", __name__)


@sound_bp.route("/sound_events")
def sound_events():
    return jsonify({
        "events": get_and_clear_sound_events()
    })  