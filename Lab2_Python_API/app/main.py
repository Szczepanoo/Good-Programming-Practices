from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from .database import SessionLocal, init_db
from .models import Movie, Link, Rating, Tag, User
import jwt
import bcrypt


app = FastAPI()
init_db()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SECRET_KEY = "super_secret_key"  # w praktyce używamy zmiennych środowiskowych
ALGORITHM = "HS256"


class LoginData(BaseModel):
    username: str
    password: str


@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": user.username,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/")
def root():
    return {"hello": "world"}


# ================================
# GET ALL

@app.get("/movies")
def get_movies(db: Session = Depends(get_db)):
    return db.query(Movie).all()


@app.get("/links")
def get_links(db: Session = Depends(get_db)):
    return db.query(Link).all()


@app.get("/ratings")
def get_ratings(db: Session = Depends(get_db)):
    return db.query(Rating).all()


@app.get("/tags")
def get_tags(db: Session = Depends(get_db)):
    return db.query(Tag).all()


# ================================
# CRUD: MOVIES

@app.post("/movies")
def create_movie(movie: dict, db: Session = Depends(get_db)):
    new_movie = Movie(**movie)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, data: dict, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    for key, value in data.items():
        setattr(movie, key, value)

    db.commit()
    db.refresh(movie)
    return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    db.delete(movie)
    db.commit()
    return {"deleted": movie_id}


# ================================
# CRUD: LINKS

@app.post("/links")
def create_link(link: dict, db: Session = Depends(get_db)):
    new_link = Link(**link)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@app.get("/links/{link_id}")
def get_link(link_id: int, db: Session = Depends(get_db)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")
    return link


@app.put("/links/{link_id}")
def update_link(link_id: int, data: dict, db: Session = Depends(get_db)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")

    for key, value in data.items():
        setattr(link, key, value)

    db.commit()
    db.refresh(link)
    return link


@app.delete("/links/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")

    db.delete(link)
    db.commit()
    return {"deleted": link_id}


# ================================
# CRUD: RATINGS

@app.post("/ratings")
def create_rating(rating: dict, db: Session = Depends(get_db)):
    new_rating = Rating(**rating)
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


@app.get("/ratings/{rating_id}")
def get_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")
    return rating


@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, data: dict, db: Session = Depends(get_db)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")

    for key, value in data.items():
        setattr(rating, key, value)

    db.commit()
    db.refresh(rating)
    return rating


@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")

    db.delete(rating)
    db.commit()
    return {"deleted": rating_id}


# ================================
# CRUD: TAGS

@app.post("/tags")
def create_tag(tag: dict, db: Session = Depends(get_db)):
    new_tag = Tag(**tag)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


@app.get("/tags/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")
    return tag


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, data: dict, db: Session = Depends(get_db)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")

    for key, value in data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")

    db.delete(tag)
    db.commit()
    return {"deleted": tag_id}
