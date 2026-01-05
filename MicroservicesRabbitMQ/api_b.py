import uuid
import json
import pika
import time
from fastapi import FastAPI, Query, HTTPException

app = FastAPI()

# RabbitMQ: używamy nazwy serwisu w docker-compose, nie localhost
RABBIT_HOST = "rabbitmq"
QUEUE_NAME = "image_tasks"
RETRY_COUNT = 5
RETRY_DELAY = 2  # sekundy

def get_rabbit_connection():
    """Tworzy połączenie do RabbitMQ z retry"""
    for i in range(RETRY_COUNT):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBIT_HOST)
            )
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(f"[RabbitMQ] Połączenie nieudane, próba {i+1}/{RETRY_COUNT}...")
            time.sleep(RETRY_DELAY)
    raise HTTPException(status_code=503, detail="Nie można połączyć się z RabbitMQ")

def publish_task(message: dict):
    """Publikuje wiadomość do kolejki z retry"""
    connection = get_rabbit_connection()
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2)  # trwała wiadomość
    )
    connection.close()

@app.post("/analyze_img")
def analyze_img(image_url: str = Query(...)):
    """Endpoint wrzucający zadanie do RabbitMQ"""
    if not image_url.startswith("http"):
        raise HTTPException(status_code=400, detail="Niepoprawny URL obrazu")

    task = {
        "task_id": str(uuid.uuid4()),
        "image_url": image_url
    }

    try:
        publish_task(task)
    except HTTPException as e:
        # RabbitMQ nieosiągalny
        raise e
    except Exception as e:
        # Inny błąd
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "queued", "task_id": task["task_id"]}
