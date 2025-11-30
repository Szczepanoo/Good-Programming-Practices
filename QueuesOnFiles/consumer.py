import csv
import msvcrt
import time
import os

QUEUE_FILE = "queue.csv"
LOCK_TIMEOUT = 10
CHUNK_SIZE = 1


def lock_file(f):
    start = time.time()
    while True:
        try:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, CHUNK_SIZE)
            return
        except OSError:
            if time.time() - start > LOCK_TIMEOUT:
                raise TimeoutError("File lock timeout.")
            time.sleep(0.05)


def unlock_file(f):
    try:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, CHUNK_SIZE)
    except:
        pass


def get_and_mark_job():
    if not os.path.exists(QUEUE_FILE):
        return None

    with open(QUEUE_FILE, "r+", newline="") as f:
        lock_file(f)

        reader = list(csv.DictReader(f))
        job = None

        for row in reader:
            if row["status"] == "pending":
                row["status"] = "in_progress"
                job = row
                break

        if job is None:
            unlock_file(f)
            return None

        f.seek(0)
        writer = csv.DictWriter(f, fieldnames=["id", "status"])
        writer.writeheader()
        writer.writerows(reader)
        f.truncate()

        unlock_file(f)
        return job


def mark_done(job_id):
    with open(QUEUE_FILE, "r+", newline="") as f:
        lock_file(f)

        rows = list(csv.DictReader(f))
        for row in rows:
            if row["id"] == str(job_id):
                row["status"] = "done"
                break

        f.seek(0)
        writer = csv.DictWriter(f, fieldnames=["id", "status"])
        writer.writeheader()
        writer.writerows(rows)
        f.truncate()

        unlock_file(f)


def work(job):
    print(f"Processing job {job['id']}...")
    time.sleep(3)
    print(f"Job {job['id']} completed.")


def consumer_loop():
    print("Consumer started.")
    while True:
        job = get_and_mark_job()
        if not job:
            time.sleep(2)
            continue

        work(job)
        mark_done(job["id"])


if __name__ == "__main__":
    consumer_loop()
