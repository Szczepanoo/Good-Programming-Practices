import os
import time
import re
import cv2
import torch
import xml.etree.ElementTree as ET
import numpy as np

from PIL import Image
from ultralytics import YOLO
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

from calculate_grade import calculate_final_grade

# =========================
# Configuration
# =========================

IMAGES_DIR = "data/images"
ANNOTATIONS_XML = "data/annotations.xml"
MODEL_PATH = "license_plate_detector.pt"

USE_GPU = torch.cuda.is_available()
DEVICE = "cuda" if USE_GPU else "cpu"

# =========================
# Models
# =========================

detector = YOLO(MODEL_PATH)
processor = TrOCRProcessor.from_pretrained("microsoft/trocr-large-printed")
trocr_model = (
    VisionEncoderDecoderModel
    .from_pretrained("microsoft/trocr-large-printed")
    .to(DEVICE)
)

# =========================
# Constants
# =========================

PLATE_REGEX = r"^[A-Z]{1,3}[A-Z0-9]{3,5}$"

LETTER_LIKE_DIGIT = {"0": "O"}

DIGIT_LIKE_LETTER = {v: k for k, v in LETTER_LIKE_DIGIT.items()}


# =========================
# Image Processing
# =========================

def crop_plate(
        image,
        bbox,
        pad_ratio=0.15,
        left_cut_ratio=0.11,
):
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


# =========================
# OCR Postprocessing
# =========================

def normalize_plate_contextual(text: str) -> str:
    if not text or len(text) < 4:
        return ""

    text = (
        re.sub(r"[^A-Z0-9]", "", text.upper())
        .replace("Q", "O")
    )

    chars = list(text)

    for i, char in enumerate(chars):
        if i < 2 and char.isdigit():
            chars[i] = LETTER_LIKE_DIGIT.get(char, char)

        elif 2 <= i <= len(chars) - 3 and char.isalpha():
            chars[i] = DIGIT_LIKE_LETTER.get(char, char)

        elif i > len(chars) - 3 and char.isdigit():
            chars[i] = LETTER_LIKE_DIGIT.get(char, char)

    return "".join(chars)


# =========================
# Detection & OCR
# =========================

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


# =========================
# Annotations
# =========================

def load_annotations(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    annotations = {}

    for image in root.findall("image"):
        image_name = image.attrib.get("name")
        box = image.find("box")

        # if box is None:
        #     continue

        plate_attr = box.find("attribute[@name='plate number']")

        # if plate_attr is None or not plate_attr.text:
        #     continue

        annotations[image_name] = plate_attr.text.strip().upper()

    return annotations


def analyze_image_bytes_trocr(image_bytes: bytes) -> dict:
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)

    bbox = detect_best_plate_bbox(image)

    text = read_plate_trocr(crop_plate(image, bbox)) if bbox else ""

    return {
        "plate": normalize_plate_contextual(text),
        "success": bool(text)
    }


# =========================
# Pipeline
# =========================

def pipeline_directory(images_dir, annotations, max_images=100):
    total = 0
    correct = 0
    elapsed = 0

    start_time = time.time()

    for image_name in sorted(os.listdir(images_dir)):

        if total == max_images:
            elapsed = time.time() - start_time

        # if image_name not in annotations:
        #     continue

        image_path = os.path.join(images_dir, image_name)
        image = cv2.imread(image_path)


        # if image is None:
        #     continue

        bbox = detect_best_plate_bbox(image)
        pred_text = read_plate_trocr(crop_plate(image, bbox)) if bbox else ""
        gt_text = normalize_plate_contextual(annotations[image_name])

        if pred_text == gt_text:
            correct += 1
            print(f"✅[DOBRZE] {image_name}: OCR -> {pred_text} | GT -> {gt_text}")
        else:
            print(f"❌[ŹLE] {image_name}: OCR -> {pred_text} | GT -> {gt_text}")

        total += 1

    accuracy = (correct / total * 100) if total else 0.0

    print(f"OCR Accuracy: {accuracy:.2f}%")
    print(f"Processed {total} images in {elapsed:.2f}s")
    print(f"Final grade: {calculate_final_grade(float(accuracy), float(elapsed))}")


# =========================
# Entry Point
# =========================

if __name__ == "__main__":
    print("CUDA available:", USE_GPU)

    if USE_GPU:
        print("CUDA device:", torch.cuda.get_device_name(0))

    annotations = load_annotations(ANNOTATIONS_XML)
    print(f"Wczytano {len(annotations)} adnotacji")

    pipeline_directory(IMAGES_DIR, annotations)
