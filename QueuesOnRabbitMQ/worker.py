import pika
import json
import cv2
import numpy as np
import requests

RABBIT_HOST = "localhost"
RABBIT_PORT = 5672
QUEUE_NAME = "image_tasks"


hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())


def download_image(url: str):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
    return cv2.imdecode(image_array, cv2.IMREAD_COLOR)


def detect_people(image):
    boxes, _ = hog.detectMultiScale(
        image,
        winStride=(8, 8),
        padding=(8, 8),
        scale=1.05
    )
    return len(boxes)


def callback(ch, method, properties, body):
    data = json.loads(body)

    task_id = data["task_id"]
    image_url = data["image_url"]

    print(f"[x] Processing task {task_id}")

    image = download_image(image_url)
    if image is None:
        print(f"[!] Task {task_id} -> Nie udało się pobrać obrazu")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    people_count = detect_people(image)
    print(f"[✓] Task {task_id} -> detected people: {people_count}")

    ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=RABBIT_PORT
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback
    )

    print("[*] Waiting for messages")
    channel.start_consuming()


if __name__ == "__main__":
    main()
