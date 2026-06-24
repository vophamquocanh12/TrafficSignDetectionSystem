import state
from services.sound_service import clear_sound_events


def get_history():
    return dict(state.history_scan)


def get_chart_data():
    return {
        "counts": dict(state.history_scan),
        "timeline": state.detection_timeline[-30:]
    }


def reset_history():
    state.history_scan.clear()
    state.last_detect_time.clear()
    state.detection_timeline.clear()
    clear_sound_events()

    return {
        "message": "Đã reset lịch sử"
    }