import sqlite3
import time

DB_FILE = "queue.db"
CHECK_INTERVAL = 2


def fetch_and_lock_job():
    conn = sqlite3.connect(DB_FILE, timeout=5)
    conn.isolation_level = "EXCLUSIVE"
    c = conn.cursor()

    try:
        c.execute("BEGIN EXCLUSIVE TRANSACTION")

        c.execute("""
            SELECT id FROM jobs
            WHERE status = 'pending'
            ORDER BY id
            LIMIT 1
        """)

        row = c.fetchone()
        if not row:
            conn.commit()
            conn.close()
            return None

        job_id = row[0]

        c.execute("""
            UPDATE jobs
            SET status = 'processing'
            WHERE id = ? AND status = 'pending'
        """, (job_id,))

        if c.rowcount == 0:
            conn.rollback()
            conn.close()
            return None

        conn.commit()
        conn.close()
        return job_id

    except sqlite3.OperationalError:
        conn.rollback()
        conn.close()
        return None


def mark_done(job_id):
    conn = sqlite3.connect(DB_FILE, timeout=5)
    c = conn.cursor()

    c.execute("""
        UPDATE jobs
        SET status = 'done'
        WHERE id = ?
    """, (job_id,))

    conn.commit()
    conn.close()


def process_job(job_id):
    print(f"Przetwarzam zadanie #{job_id}...")
    time.sleep(3)  # symulacja pracy
    print(f"Zakończono zadanie #{job_id}")


def loop():
    while True:
        job_id = fetch_and_lock_job()
        if job_id is None:
            time.sleep(CHECK_INTERVAL)
            continue

        process_job(job_id)
        mark_done(job_id)


if __name__ == "__main__":
    loop()
