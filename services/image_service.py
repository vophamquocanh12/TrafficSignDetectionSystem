import cv2
import numpy as np

import state
from services.model_service import detect_frame


def process_image(file):
    file_bytes = file.read()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return False

    output = detect_frame(frame)

    success, buffer = cv2.imencode(".jpg", output)

    if not success:
        return False

    state.latest_output_data = buffer.tobytes()
    state.latest_output_type = "image"

    return True