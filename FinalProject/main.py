import os
import time
import re
import cv2
import xml.etree.ElementTree as ET
from typing import Dict, List

import easyocr
from ultralytics import YOLO


# =========================
# Konfiguracja
# =========================

IMAGES_DIR = "data/images"
ANNOTATIONS_XML = "data/annotations.xml"
MODEL_PATH = "license_plate_detector.pt"

MAX_IMAGES = 195
OCR_LANGS = ["en"]
USE_GPU = True

PLATE_REGEX = re.compile(r"^[A-Z]{1,3}[A-Z0-9]{3,5}$")

# Procenty docinania bboxa (tuning OCR)
CROP_CONFIG = {
    "left": 0.13,
    "right": 0.05,
    "top": 0.02,
    "bottom": 0.02,
}

# =========================
# Inicjalizacja modeli
# =========================

ocr_reader = easyocr.Reader(OCR_LANGS, gpu=USE_GPU)
detector = YOLO(MODEL_PATH)


# =========================
# OCR – scoring i selekcja
# =========================

def score_plate_candidate(text: str) -> int:
    score = 0

    if 5 <= len(text) <= 8:
        score += 2
    else:
        score -= 2

    if PLATE_REGEX.match(text):
        score += 5

    if text and text[0].isalpha():
        score += 1

    digits_count = sum(char.isdigit() for char in text)
    if digits_count > len(text) - 2:
        score -= 1

    return score


def pick_best_ocr_result(results: List[str]) -> str:
    best_text = ""
    best_score = float("-inf")

    for raw_text in results:
        text = raw_text.replace(" ", "").upper()

        if not 4 <= len(text) <= 8:
            continue

        score = score_plate_candidate(text)
        if score > best_score:
            best_score = score
            best_text = text

    return best_text


# =========================
# OCR – przetwarzanie obrazu
# =========================

def crop_plate(image, bbox):
    x1, y1, x2, y2 = bbox
    width, height = x2 - x1, y2 - y1

    x1 += int(CROP_CONFIG["left"] * width)
    x2 -= int(CROP_CONFIG["right"] * width)
    y1 += int(CROP_CONFIG["top"] * height)
    y2 -= int(CROP_CONFIG["bottom"] * height)

    if x2 <= x1 or y2 <= y1:
        return None

    return image[y1:y2, x1:x2]


def preprocess_for_ocr(crop):
    resized = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)


def read_plate_easyocr(image, bbox) -> str:
    crop = crop_plate(image, bbox)
    if crop is None:
        return ""

    processed = preprocess_for_ocr(crop)

    results = ocr_reader.readtext(
        processed,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        detail=0,
    )

    return pick_best_ocr_result(results) if results else ""


# =========================
# Normalizacja
# =========================

def normalize_plate(text: str) -> str:
    if not text:
        return ""

    mapping = {
        "0": "O",
        "O": "O",
    }

    return "".join(mapping.get(char, char) for char in text)


# =========================
# Dane – XML
# =========================

def load_annotations(xml_path: str) -> Dict[str, str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()

    annotations = {}

    for image in root.findall("image"):
        img_name = image.attrib.get("name")
        box = image.find("box")
        if box is None:
            continue

        plate_attr = box.find("attribute[@name='plate number']")
        if plate_attr is None or not plate_attr.text:
            continue

        annotations[img_name] = plate_attr.text.strip().upper()

    return annotations


# =========================
# Detekcja
# =========================

def detect_best_plate_bbox(image):
    results = detector(image, verbose=False)

    if not results or not results[0].boxes:
        return None

    boxes = results[0].boxes
    best_box = max(boxes, key=lambda b: b.conf[0])

    return best_box.xyxy[0].cpu().numpy().astype(int).tolist()


# =========================
# Main loop
# =========================

def main():
    annotations = load_annotations(ANNOTATIONS_XML)
    print(f"Wczytano {len(annotations)} adnotacji")

    image_files = sorted(os.listdir(IMAGES_DIR))

    total = 0
    correct = 0
    start_time = time.time()

    for img_name in image_files:
        if img_name not in annotations or total >= MAX_IMAGES:
            continue

        image_path = os.path.join(IMAGES_DIR, img_name)
        image = cv2.imread(image_path)
        if image is None:
            continue

        bbox = detect_best_plate_bbox(image)
        pred_text = read_plate_easyocr(image, bbox) if bbox else ""

        gt_text = annotations[img_name]

        pred_text = normalize_plate(pred_text)
        gt_text = normalize_plate(gt_text)

        if pred_text == gt_text:
            correct += 1
        else:
            print(f"[ŹLE] {img_name}: OCR -> {pred_text} | GT -> {gt_text}")

        total += 1

    elapsed = time.time() - start_time
    accuracy = (correct / total * 100) if total else 0

    print(f"OCR Accuracy: {accuracy:.2f}%")
    print(f"Processing time for {total} images: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
