import json
import requests
import pika
import time

RABBIT_HOST = "rabbitmq"
RESULT_QUEUE = "results_retry"
SERVICE_A_URL = "http://service-a:8000/results"
RETRY_COUNT = 8
RETRY_DELAY = 5

time.sleep(5)

def callback(ch, method, properties, body):
    result = json.loads(body)

    try:
        r = requests.post(SERVICE_A_URL, json=result, timeout=5)
        r.raise_for_status()
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"Service A unavailable, retrying later: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

connection = None
for i in range(RETRY_COUNT):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=RABBIT_HOST)
        )
        print("Połączono z RabbitMQ", flush=True)
        break
    except pika.exceptions.AMQPConnectionError:
        print(f"[RabbitMQ] Połączenie nieudane, próba {i + 1}/{RETRY_COUNT}...", flush=True)
        time.sleep(RETRY_DELAY)

if connection is None:
    raise RuntimeError("Nie udało się połączyć z RabbitMQ po kilku próbach")

channel = connection.channel()
channel.queue_declare(queue=RESULT_QUEUE, durable=True)
channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=RESULT_QUEUE, on_message_callback=callback, auto_ack=False)

print("Result sender waiting")
channel.start_consuming()
