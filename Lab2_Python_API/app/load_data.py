import csv
from .database import engine, SessionLocal
from .models import Movie, Link, Rating, Tag, Base
import os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_DIR = os.path.join(BASE_DIR, "database")

print(">>> Using CSV_DIR:", CSV_DIR)

def load_movies(db):
    with open(os.path.join(CSV_DIR, "movies.csv"), encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Movie(
                movieId=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"]
            ))
    db.commit()


def load_links(db):
    with open(os.path.join(CSV_DIR, "links.csv"), encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Link(
                movieId=int(row["movieId"]),
                imdbId=row["imdbId"],
                tmdbId=row["tmdbId"]
            ))
    db.commit()


def load_ratings(db):
    with open(os.path.join(CSV_DIR, "ratings.csv"), encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Rating(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            ))
    db.commit()


def load_tags(db):
    with open(os.path.join(CSV_DIR, "tags.csv"), encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            db.add(Tag(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                tag=row["tag"],
                timestamp=int(row["timestamp"])
            ))
    db.commit()


def load_all():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    load_movies(db)
    load_links(db)
    load_ratings(db)
    load_tags(db)
    db.close()


if __name__ == "__main__":
    load_all()
