import cv2
import time
import tempfile
import threading

import state
from services.model_service import detect_frame


def upload_and_start_video(file):
    state.video_session_id += 1
    my_session = state.video_session_id

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".mp4"
    )

    file.save(temp_file.name)
    temp_file.close()

    input_path = temp_file.name

    state.latest_video_input_path = input_path
    state.latest_output_type = "video"

    with state.current_video_lock:
        state.current_video["raw_frame"] = None
        state.current_video["detect_frame"] = None
        state.current_video["running"] = True
        state.current_video["paused"] = False
        state.current_video["finished"] = False
        state.current_video["session"] = my_session

    thread = threading.Thread(
        target=process_video,
        args=(input_path, my_session),
        daemon=True
    )

    thread.start()

    return my_session


def process_video(input_path, my_session):
    cap = cv2.VideoCapture(input_path)

    fps = cap.get(cv2.CAP_PROP_FPS)

    if fps <= 0:
        fps = 25

    delay = 1 / fps
    frame_count = 0
    last_detect = None

    while True:
        start_time = time.time()

        with state.current_video_lock:
            if state.current_video["session"] != my_session:
                break

            if not state.current_video["running"]:
                break

            paused = state.current_video["paused"]

        if paused:
            time.sleep(0.05)
            continue

        success, frame = cap.read()

        if not success:
            break

        frame_count += 1
        raw_frame = frame.copy()

        if frame_count % 4 == 0 or last_detect is None:
            last_detect = detect_frame(frame.copy())

        with state.current_video_lock:
            if state.current_video["session"] != my_session:
                break

            state.current_video["raw_frame"] = raw_frame
            state.current_video["detect_frame"] = last_detect.copy()

        elapsed = time.time() - start_time
        sleep_time = max(0, delay - elapsed)
        time.sleep(sleep_time)

    cap.release()

    with state.current_video_lock:
        if state.current_video["session"] == my_session:
            state.current_video["running"] = False
            state.current_video["finished"] = True


def pause_video():
    with state.current_video_lock:
        state.current_video["paused"] = True


def resume_video():
    with state.current_video_lock:
        state.current_video["paused"] = False


def stop_video():
    with state.current_video_lock:
        state.current_video["running"] = False
        state.current_video["paused"] = False
        state.current_video["finished"] = True
        state.current_video["raw_frame"] = None
        state.current_video["detect_frame"] = None