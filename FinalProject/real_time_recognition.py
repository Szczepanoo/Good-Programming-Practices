import os
import time
import re
import cv2
import torch
import numpy as np
from PIL import Image
from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

# ======================================================
# Configuration
# ======================================================

MODEL_PATH = "license_plate_detector.pt"
PLATES_DB_PATH = "allowed_plates.txt"

CAMERA_INDEX = 0
OCR_EVERY_N_FRAMES = 5
ACCESS_COOLDOWN_SEC = 5
OCR_PAUSE_AFTER_ACCESS_SEC = 10

USE_GPU = torch.cuda.is_available()
DEVICE = "cuda" if USE_GPU else "cpu"

# ======================================================
# Models
# ======================================================

detector = YOLO(MODEL_PATH)

processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-printed")
trocr_model = (
    VisionEncoderDecoderModel
    .from_pretrained("microsoft/trocr-large-printed")
    .to(DEVICE)
    .eval()
)

# ======================================================
# OCR Postprocessing
# ======================================================

LETTER_LIKE_DIGIT = {"0": "O"}
DIGIT_LIKE_LETTER = {v: k for k, v in LETTER_LIKE_DIGIT.items()}

def normalize_plate_contextual(text: str) -> str:
    if not text or len(text) < 4:
        return ""

    text = re.sub(r"[^A-Z0-9]", "", text.upper()).replace("Q", "O")
    chars = list(text)

    for i, char in enumerate(chars):
        if i < 2 and char.isdigit():
            chars[i] = LETTER_LIKE_DIGIT.get(char, char)
        elif 2 <= i <= len(chars) - 3 and char.isalpha():
            chars[i] = DIGIT_LIKE_LETTER.get(char, char)
        elif i > len(chars) - 3 and char.isdigit():
            chars[i] = LETTER_LIKE_DIGIT.get(char, char)

    return "".join(chars)

# ======================================================
# Image Processing
# ======================================================

def crop_plate(image, bbox, pad_ratio=0.15, left_cut_ratio=0.11):
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]

    pad_x = int((x2 - x1) * 0.03)
    pad_y = int((y2 - y1) * pad_ratio)

    x1 = max(0, x1 - pad_x)
    x2 = min(w, x2 + pad_x)
    y1 = max(0, y1 - pad_y)
    y2 = min(h, y2 + pad_y)

    cropped = image[y1:y2, x1:x2]
    _, cw = cropped.shape[:2]

    left_cut = int(cw * left_cut_ratio)
    return cropped[:, left_cut:]

# ======================================================
# Detection & OCR
# ======================================================

def detect_best_plate_bbox(image):
    results = detector(image, verbose=False)

    if not results or not results[0].boxes:
        return None

    best_box = max(
        results[0].boxes,
        key=lambda b: float(b.conf[0].cpu())
    )

    x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()
    return [int(x1), int(y1), int(x2), int(y2)]

def read_plate_trocr(cropped_plate):
    pil_img = Image.fromarray(
        cv2.cvtColor(cropped_plate, cv2.COLOR_BGR2RGB)
    )

    pixel_values = processor(
        pil_img,
        return_tensors="pt"
    ).pixel_values.to(DEVICE)

    with torch.no_grad():
        generated_ids = trocr_model.generate(
            pixel_values,
            max_new_tokens=8,
            num_beams=1
        )

    text = processor.batch_decode(
        generated_ids,
        skip_special_tokens=True
    )[0]

    return normalize_plate_contextual(text)

# ======================================================
# Access Control
# ======================================================

def load_allowed_plates(path: str) -> set:
    if not os.path.exists(path):
        print("⚠️ Brak pliku bazy tablic")
        return set()

    with open(path, "r", encoding="utf-8") as f:
        plates = {
            normalize_plate_contextual(line.strip())
            for line in f
            if line.strip()
        }

    print(f"Wczytano {len(plates)} tablic do bazy")
    return plates

def has_access(plate: str, allowed_plates: set) -> bool:
    return plate in allowed_plates

# ======================================================
# Camera Loop
# ======================================================

def run_camera_lpr():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        raise RuntimeError("Nie można otworzyć kamery")

    allowed_plates = load_allowed_plates(PLATES_DB_PATH)

    frame_id = 0
    last_plate_text = ""
    last_access_time = 0
    ocr_paused_until = 0

    print("Start LPR + Szlaban | ESC = wyjście")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        bbox = detect_best_plate_bbox(frame)

        if bbox:
            now = time.time()

            if now >= ocr_paused_until and frame_id % OCR_EVERY_N_FRAMES == 0:
                cropped = crop_plate(frame, bbox)
                text = read_plate_trocr(cropped)

                if text:
                    last_plate_text = text

                    if has_access(text, allowed_plates) and now - last_access_time > ACCESS_COOLDOWN_SEC:
                        print(f"✅ {text} – Otwieram szlaban")
                        last_access_time = now
                        ocr_paused_until = now + OCR_PAUSE_AFTER_ACCESS_SEC

                    else:
                        print(f"❌ {text} – Brak dostępu")

            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if last_plate_text:
                cv2.putText(
                    frame,
                    last_plate_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2
                )

        cv2.imshow("LPR – Access Control", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

        frame_id += 1

    cap.release()
    cv2.destroyAllWindows()

# ======================================================
# Entry Point
# ======================================================

if __name__ == "__main__":
    print("CUDA available:", USE_GPU)
    if USE_GPU:
        print("CUDA device:", torch.cuda.get_device_name(0))

    run_camera_lpr()
