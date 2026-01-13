import os
import time
import re
import cv2
import xml.etree.ElementTree as ET
from typing import Dict, List
import torch
import easyocr
from ultralytics import YOLO
import numpy as np
from calculate_grade import calculate_final_grade


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
    "left": 0.05,
    "right": 0.13,
    "top": 0.02,
    "bottom": 0.02,
}
LETTER_LIKE_DIGIT = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "5": "S",
    "6": "G",
    "8": "B",
    "4": "A"
}

DIGIT_LIKE_LETTER = {
    "O": "0",
    "I": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "B": "8",
    "A": "4"
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
    else:
        score -= 3

    if text[0] not in "SKWPDLZNRTOEF":
        score -= 3

    if text and text[0].isalpha():
        score += 1

    digits_count = sum(char.isdigit() for char in text)
    if digits_count > len(text) - 2:
        score -= 1

    if digits_count == 0:
        score -= 5

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


def bbox_score(box):
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

    w = x2 - x1
    h = y2 - y1
    area = w * h

    conf = float(box.conf[0].cpu().item())
    aspect = w / (h + 1e-6)

    aspect_penalty = 1.0 if 2.5 < aspect < 6.0 else 0.6
    return conf * (area ** 0.5) * aspect_penalty




# =========================
# OCR – przetwarzanie obrazu
# =========================

def crop_plate(image, bbox):
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]

    pad_x = int(0.03 * (x2 - x1))
    pad_y = int(0.15 * (y2 - y1))

    x1 = max(0, x1 - pad_x)
    x2 = min(w, x2 + pad_x)
    y1 = max(0, y1 - pad_y)
    y2 = min(h, y2 + pad_y)

    return image[y1:y2, x1:x2]


def preprocess_for_detection(image):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    lab = cv2.merge((l, a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def preprocess_primary(crop):
    resized = cv2.resize(
        crop, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC
    )
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    return cv2.cvtColor(enhanced, cv2.COLOR_GRAY2RGB)


def preprocess_fallback(crop):
    # skalowanie
    resized = cv2.resize(
        crop, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR
    )
    # grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # lekki blur do wygładzenia szumu
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    # OCR wymaga 3 kanałów
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

def preprocess_for_ocr_morphology(crop):
    """
    Ultra-łagodny preprocessing pod OCR:
    - grayscale + CLAHE,
    - blackhat (bardzo mały kernel),
    - lekki gradient w poziomie,
    - minimalny closing i erozja/dylacja,
    - OCR wymaga 3 kanałów.
    """
    # --- grayscale + CLAHE ---
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # --- blackhat morphologia (ultra mały kernel) ---
    rec_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 2))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, rec_kernel)

    # --- gradient w poziomie (Sobel) ---
    grad_x = cv2.Sobel(blackhat, ddepth=cv2.CV_32F, dx=1, dy=0, ksize=-1)
    grad_x = np.absolute(grad_x)
    grad_x = cv2.normalize(grad_x, None, 0, 255, cv2.NORM_MINMAX).astype("uint8")

    # --- minimalne closing ---
    square_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 1))
    closed = cv2.morphologyEx(grad_x, cv2.MORPH_CLOSE, square_kernel)

    # --- łagodna threshold + minimalne czyszczenie ---
    _, thresh = cv2.threshold(closed, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    thresh = cv2.erode(thresh, None, iterations=0)
    thresh = cv2.dilate(thresh, None, iterations=1)

    # --- debug ---
    cv2.imshow("OCR Morphology - Ultra Light", thresh)
    cv2.waitKey(0)

    # OCR wymaga 3 kanałów
    return cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)




def upscale_if_needed(image, min_width=960):
    h, w = image.shape[:2]
    if w < min_width:
        scale = min_width / w
        image = cv2.resize(
            image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC
        )
    return image


def read_plate_easyocr(image, bbox) -> str:
    crop = crop_plate(image, bbox)
    if crop is None:
        return ""

    processed = preprocess_primary(crop)

    results = ocr_reader.readtext(
        processed,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        detail=0,
    )

    return pick_best_ocr_result(results) if results else ""


def read_plate_easyocr_with_fallback(image, bbox) -> str:
    crop = crop_plate(image, bbox)
    if crop is None:
        return ""

    # ---------- PASS 1 ----------
    primary_img = preprocess_primary(crop)
    #primary_img = preprocess_for_ocr_morphology(crop)
    result = ocr_reader.readtext(
        primary_img,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        detail=0,
        #decoder="beamsearch"
    )

    text = pick_best_ocr_result(result) if result else ""
    if text:
        return text

    # ---------- PASS 2 (fallback) ----------
    fallback_img = preprocess_fallback(crop)
    result = ocr_reader.readtext(
        fallback_img,
        allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        detail=0,
        contrast_ths=0.1,
        adjust_contrast=0.7,
    )

    return pick_best_ocr_result(result) if result else ""


# =========================
# Normalizacja
# =========================

def normalize_plate_contextual(text: str) -> str:
    if not text or len(text) < 4:
        return ""

    text = text.upper()
    chars = list(text)

    for i, c in enumerate(chars):
        # początek – litery
        if i < 2:
            if c.isdigit():
                chars[i] = LETTER_LIKE_DIGIT.get(c, c)

        # środek – cyfry
        elif 2 <= i <= len(chars) - 3:
            if c.isalpha():
                chars[i] = DIGIT_LIKE_LETTER.get(c, c)

        # końcówka – preferuj litery
        else:
            if c.isdigit():
                chars[i] = LETTER_LIKE_DIGIT.get(c, c)

    return "".join(chars)



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
    h0, w0 = image.shape[:2]
    det_img = upscale_if_needed(image)
    h1, w1 = det_img.shape[:2]

    scale_x = w0 / w1
    scale_y = h0 / h1

    results = detector(det_img, verbose=False)
    if not results or not results[0].boxes:
        return None

    boxes = results[0].boxes
    best_box = max(boxes, key=bbox_score)

    x1, y1, x2, y2 = best_box.xyxy[0].cpu().numpy()

    return [
        int(x1 * scale_x),
        int(y1 * scale_y),
        int(x2 * scale_x),
        int(y2 * scale_y),
    ]


def analyze_image_bytes(image_bytes: bytes) -> dict:
    image = cv2.imdecode(
        np.frombuffer(image_bytes, np.uint8),
        cv2.IMREAD_COLOR
    )

    bbox = detect_best_plate_bbox(image)
    text = read_plate_easyocr_with_fallback(image, bbox) if bbox else ""

    return {
        "plate": normalize_plate_contextual(text),
        "success": bool(text)
    }


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
        pred_text = (
            read_plate_easyocr_with_fallback(image, bbox)
        if bbox else ""
        )

        gt_text = annotations[img_name]

        pred_text = normalize_plate_contextual(pred_text)
        gt_text = normalize_plate_contextual(gt_text)

        if pred_text == gt_text:
            correct += 1
        else:
            print(
                f"[ŹLE] {img_name}: OCR -> {pred_text} | GT -> {gt_text}"
            )

        total += 1

    elapsed = time.time() - start_time
    accuracy = (correct / total * 100) if total else 0

    print(f"OCR Accuracy: {accuracy:.2f}%")
    print(f"Processing time for {total} images: {elapsed:.2f}s")
    #print(f"Final grade: {calculate_final_grade(total, elapsed:.2f}")


if __name__ == "__main__":
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA device:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "NONE")
    main()
