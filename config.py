MODEL_PATH = "runs/detect/traffic_sign_warning_model/weights/best.pt"

CLASS_NAMES = {
    0: "Đường người đi bộ cắt ngang",
    1: "Trẻ em",
    2: "Công trường",
    3: "Giao nhau với đường ưu tiên",
    4: "Giao nhau có tín hiệu đèn",
    5: "Đường giao nhau"
}

DETECT_COOLDOWN = 3

CLASS_COLORS = {
    0: (18, 193, 12),      # #0cc112
    1: (245, 0, 245),      # #f500f5
    2: (13, 29, 255),      # #ff1d0d
    3: (243, 150, 33),     # #2196f3
    4: (156, 39, 176),     # #9c27b0
    5: (72, 85, 121)       # #795548
}