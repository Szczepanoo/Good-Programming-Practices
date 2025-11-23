from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import Movie, Link, Rating, Tag

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import inspect
from .database import engine

insp = inspect(engine)
print(">>> TABLES IN DB:", insp.get_table_names())

@app.get("/")
def root():
    return {"hello": "world"}


@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    movies = db.query(Movie).all()
    return [m.__dict__ for m in movies]


@app.get("/links")
def get_links(db: Session = Depends(get_db)):
    links = db.query(Link).all()
    return [l.__dict__ for l in links]


@app.get("/ratings")
def get_ratings(db: Session = Depends(get_db)):
    ratings = db.query(Rating).all()
    return [r.__dict__ for r in ratings]


@app.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return [t.__dict__ for t in tags]
