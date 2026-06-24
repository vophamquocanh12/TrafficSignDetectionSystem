from collections import defaultdict
import threading


history_scan = defaultdict(int)
detection_timeline = []
last_detect_time = {}

sound_events = []
sound_lock = threading.Lock()

camera = None
latest_frame = None
latest_detect_frame = None
camera_running = False
camera_lock = threading.Lock()

latest_output_data = None
latest_output_type = None
latest_video_input_path = None

current_video = {
    "raw_frame": None,
    "detect_frame": None,
    "running": False,
    "paused": False,
    "finished": False,
    "session": 0
}

current_video_lock = threading.Lock()
video_session_id = 0