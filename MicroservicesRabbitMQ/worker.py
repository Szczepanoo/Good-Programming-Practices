import json
import time
import requests
import pika
import cv2
import numpy as np

time.sleep(5)

# --- Konfiguracja ---
RABBIT_HOST = "rabbitmq"  # Docker Compose service name
TASK_QUEUE = "image_tasks"
RESULT_QUEUE = "results_retry"
SERVICE_A_URL = "http://service-a:8000/results"

RETRY_COUNT = 8
RETRY_DELAY = 5  # sekundy

# --- Detektor ludzi (OpenCV HOG) ---
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# --- Funkcja wykrywająca ludzi ---
def detect_people(image_url: str) -> int:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WorkerBot/1.0)"
        }
        resp = requests.get(image_url, timeout=10, headers=headers)
        if resp.status_code != 200:
            raise ValueError(f"Nie udało się pobrać obrazu, status: {resp.status_code}")
        img_array = np.frombuffer(resp.content, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Nie udało się wczytać obrazu przez OpenCV")
        img = cv2.resize(img, (640, 480))
        boxes, _ = hog.detectMultiScale(img)
        return len(boxes)
    except Exception as e:
        print(f"[detect_people] Błąd: {e}",flush=True)
        return -1  # sygnalizuje niepowodzenie

# --- Funkcja do połączenia z RabbitMQ z retry ---
def get_rabbit_connection():
    for i in range(RETRY_COUNT):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            print("Połączono z RabbitMQ",flush=True)
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"[RabbitMQ] Połączenie nieudane, próba {i+1}/{RETRY_COUNT}...",flush=True)
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Nie udało się połączyć z RabbitMQ po kilku próbach")

# --- Callback dla tasków ---
def callback(ch, method, properties, body):
    task = json.loads(body)
    task_id = task["task_id"]
    image_url = task["image_url"]

    try:
        count = detect_people(image_url)
        if count == -1:
            # Błąd w analizie, nie ack, task zostaje w kolejce
            print(f"[Worker] Analiza nie powiodła się dla task {task_id}, retry...",flush=True)
            time.sleep(2)
            return

        result = {
            "task_id": task_id,
            "image_url": image_url,
            "detected_people": count
        }

        # Wysyłanie wyniku do kolejki wynikowej
        for attempt in range(RETRY_COUNT):
            try:
                result_connection = get_rabbit_connection()
                result_channel = result_connection.channel()
                result_channel.queue_declare(queue=RESULT_QUEUE, durable=True)

                result_channel.basic_publish(
                    exchange="",
                    routing_key=RESULT_QUEUE,
                    body=json.dumps(result),
                    properties=pika.BasicProperties(delivery_mode=2)
                )
                result_connection.close()
                print(f"[Worker] Task {task_id} przetworzony, znaleziono {count} osób",flush=True)
                break
            except Exception as e:
                print(f"[Worker] Nie udało się wysłać wyniku, próba {attempt+1}: {e}",flush=True)
                time.sleep(2)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[Worker] Błąd w callback: {e}")
        time.sleep(2)

# --- Główna pętla workera ---
connection = get_rabbit_connection()
channel = connection.channel()
channel.queue_declare(queue=TASK_QUEUE, durable=True)
channel.queue_declare(queue=RESULT_QUEUE, durable=True)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=TASK_QUEUE, on_message_callback=callback)

print("[Worker] Czekam na zadania...",flush=True)
channel.start_consuming()
