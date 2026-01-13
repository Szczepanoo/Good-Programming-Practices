import pika
import sqlite3
from datetime import datetime
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
    cursor.execute(
        "INSERT INTO results (plate, success, created_at) VALUES (?, ?, ?)",
        (
            result["plate"],
            int(result["success"]),
            datetime.utcnow().isoformat()
        )
    )
    conn.commit()


# ---------- Rabbit ----------
connection = pika.BlockingConnection(
    pika.ConnectionParameters("localhost",5672)
)
channel = connection.channel()
channel.queue_declare(queue="ocr_queue", durable=True)


def callback(ch, method, properties, body):
    result = analyze_image_bytes(body)
    save(result)
    ch.basic_ack(method.delivery_tag)


print("Worker started...")
channel.basic_consume(
    queue="ocr_queue",
    on_message_callback=callback
)
channel.start_consuming()
