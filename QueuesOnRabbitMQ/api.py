from fastapi import FastAPI
import pika
import json
import uuid

app = FastAPI()

RABBIT_HOST = "localhost"
RABBIT_PORT = 5672
QUEUE_NAME = "image_tasks"


def publish_task(image_url: str, task_id: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBIT_HOST,
            port=RABBIT_PORT
        )
    )

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    message = {
        "task_id": task_id,
        "image_url": image_url
    }

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    connection.close()


@app.post("/analyze_img")
def analyze_image(image_url: str):
    task_id = str(uuid.uuid4())
    publish_task(image_url, task_id)

    return {
        "task_id": task_id,
        "status": "queued"
    }
