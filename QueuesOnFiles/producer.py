import csv
import os

QUEUE_FILE = "queue.csv"


def write_job():
    file_exists = os.path.isfile(QUEUE_FILE)

    if not file_exists:
        with open(QUEUE_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "status"])

    last_id = 0
    with open(QUEUE_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            last_id = int(row["id"])

    new_id = last_id + 1

    with open(QUEUE_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([new_id, "pending"])

    print(f"Dodałem pracę #{new_id} (pending)")


if __name__ == "__main__":
    for _ in range(20):
        write_job()
