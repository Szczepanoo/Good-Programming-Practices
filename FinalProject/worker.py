import pika
import sqlite3
from datetime import datetime, UTC
from ocr import analyze_image_bytes

# ---------- DB ----------
conn = sqlite3.connect("results.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plate TEXT,
    success INTEGER,
    created_at TEXT
)
""")
conn.commit()


def save(result):
    print(f"[INFO] Zapisuję wynik: {result}")
    cursor.execute(
        "INSERT INTO results (plate, success, created_at) VALUES (?, ?, ?)",
        (
            result["plate"],
            int(result["success"]),
            datetime.now(UTC).isoformat()
        )
    )
    conn.commit()


# ---------- Rabbit ----------
print("[INFO] Łączenie z RabbitMQ...")
connection = pika.BlockingConnection(
    pika.ConnectionParameters("localhost",5672)
)
channel = connection.channel()
channel.queue_declare(queue="ocr_queue", durable=True)
print("[INFO] Połączono, oczekiwanie na wiadomości...")

def callback(ch, method, properties, body):
    print(f"[INFO] Przetwarzanie wiadomości: {method.delivery_tag}")
    result = analyze_image_bytes(body)
    save(result)
    ch.basic_ack(method.delivery_tag)


channel.basic_consume(
    queue="ocr_queue",
    on_message_callback=callback
)
channel.start_consuming()
