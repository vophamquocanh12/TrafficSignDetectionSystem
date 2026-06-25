import time
import cv2
from ultralytics import YOLO

import state
from config import MODEL_PATH, CLASS_NAMES, DETECT_COOLDOWN, CLASS_COLORS
from services.sound_service import add_sound_event

model = YOLO(MODEL_PATH)


from PIL import Image, ImageDraw, ImageFont
import numpy as np

def detect_frame(frame):
    results = model.predict(
        frame,
        conf=0.45,
        imgsz=320,
        verbose=False
    )

    annotated = frame.copy()

    if results[0].boxes is not None:

        # Chuyển sang PIL để vẽ tiếng Việt
        pil_img = Image.fromarray(
            cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
        )

        draw = ImageDraw.Draw(pil_img)

        font = ImageFont.truetype(
            "C:/Windows/Fonts/arial.ttf",
            20
        )

        for box in results[0].boxes:

            class_id = int(box.cls[0])
            class_name = CLASS_NAMES.get(class_id, "Unknown")

            conf = float(box.conf[0])
            conf_percent = round(conf * 100, 1)

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # Giữ nguyên màu xanh như hiện tại
            color_cv = CLASS_COLORS.get(class_id, (0, 255, 0))

            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                color_cv,
                2
            )

            # Đồng bộ PIL sau khi vẽ rectangle
            pil_img = Image.fromarray(
                cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            )

            draw = ImageDraw.Draw(pil_img)

            label = f"{class_name} ({conf_percent}%)"

            text_color = (
                color_cv [2],
                color_cv [1],
                color_cv [0]
            )

            draw.text(
                (x1, max(0, y1 - 28)),
                label,
                font=font,
                fill=text_color
            )

            annotated = cv2.cvtColor(
                np.array(pil_img),
                cv2.COLOR_RGB2BGR
            )

            current_time = time.time()

            if class_name not in state.last_detect_time:
                update_detection(
                    class_name,
                    current_time
                )

            elif current_time - state.last_detect_time[class_name] > DETECT_COOLDOWN:
                update_detection(
                    class_name,
                    current_time
                )

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