import time
import cv2
from ultralytics import YOLO

import state
from config import MODEL_PATH, CLASS_NAMES, DETECT_COOLDOWN
from services.sound_service import add_sound_event

model = YOLO(MODEL_PATH)


def detect_frame(frame):
    results = model.predict(
        frame,
        conf=0.45,
        imgsz=320,
        verbose=False
    )

    annotated = results[0].plot(
        conf=False,
        labels=True
    )

    if results[0].boxes is not None:
        for box in results[0].boxes:
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES.get(class_id, "Unknown")
            current_time = time.time()

            if class_name not in state.last_detect_time:
                update_detection(class_name, current_time)

            elif current_time - state.last_detect_time[class_name] > DETECT_COOLDOWN:
                update_detection(class_name, current_time)

    return annotated


def update_detection(class_name, current_time):
    state.history_scan[class_name] += 1
    state.last_detect_time[class_name] = current_time

    state.detection_timeline.append({
        "time": time.strftime("%H:%M:%S"),
        "class_name": class_name
    })

    add_sound_event(class_name)


def encode_jpg(frame):
    ret, buffer = cv2.imencode(".jpg", frame)

    if not ret:
        return None

    return buffer.tobytes()
    ret, buffer = cv2.imencode(".jpg", frame)

    if not ret:
        return None

    return buffer.tobytes()