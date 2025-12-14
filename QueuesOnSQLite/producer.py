import sqlite3
import argparse

DB_FILE = "queue.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL CHECK (status IN ('pending', 'processing', 'done'))
        );
    """)

    conn.commit()
    conn.close()


def add_job():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("INSERT INTO jobs (status) VALUES ('pending')")
    conn.commit()

    job_id = c.lastrowid
    conn.close()

    print(f"Dodałem pracę #{job_id} (pending)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uruchomienie aplikacji")
    parser.add_argument(
        "--jobs",
        type=int,
        default=1,
        help="Liczba zadań do dodania"
    )

    args = parser.parse_args()

    init_db()
    for _ in range(args.jobs):
        add_job()
