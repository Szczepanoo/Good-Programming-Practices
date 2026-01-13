from fastapi import FastAPI, UploadFile, File
import pika
from ocr import analyze_image_bytes

app = FastAPI()

@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = analyze_image_bytes(image_bytes)
    return result


@app.post("/enqueue")
async def enqueue(file: UploadFile = File(...)):
    image_bytes = await file.read()

    params = pika.ConnectionParameters(
        host="localhost",
        port=5672,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue="ocr_queue", durable=True)

    channel.basic_publish(
        exchange="",
        routing_key="ocr_queue",
        body=image_bytes
    )

    connection.close()

    return {"status": "queued"}

