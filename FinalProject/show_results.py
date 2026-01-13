import sqlite3

DB_PATH = "results.db"

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT id, plate, success, created_at FROM results")
    rows = cursor.fetchall()

    if not rows:
        print("Baza jest pusta.")
        return

    print(f"{'ID':<5} {'PLATE':<12} {'OK':<5} {'CREATED_AT'}")
    print("-" * 50)

    for row in rows:
        id_, plate, success, created_at = row
        print(f"{id_:<5} {plate or '-':<12} {success:<5} {created_at}")

    conn.close()


if __name__ == "__main__":
    main()
