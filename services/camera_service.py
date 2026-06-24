import cv2
import threading

camera = None
latest_frame = None
camera_lock = threading.Lock()
camera_running = False


def start_camera_thread():
    global camera
    global latest_frame
    global camera_running

    if camera_running:
        return

    camera_running = True
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    def update():
        global latest_frame

        while camera_running:
            success, frame = camera.read()

            if success:
                with camera_lock:
                    latest_frame = frame.copy()

    thread = threading.Thread(
        target=update,
        daemon=True
    )

    thread.start()


def stop_camera_service():
    global camera
    global latest_frame
    global camera_running

    camera_running = False

    if camera:
        camera.release()
        camera = None

    latest_frame = None


def get_latest_frame():
    with camera_lock:
        if latest_frame is None:
            return None

        return latest_frame.copy()