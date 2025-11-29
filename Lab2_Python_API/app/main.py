from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from .database import SessionLocal, init_db
from .models import Movie, Link, Rating, Tag, User
import jwt
import bcrypt
from sqlalchemy import cast, Boolean

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


bearer_scheme = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def require_admin(current_user: User):
    roles = current_user.roles.split(",")
    if "ROLE_ADMIN" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required"
        )


@app.post("/login")
def login(data: LoginData, db: Session = Depends(get_db)):
    user = db.query(User).filter(cast(User.username == data.username, Boolean)).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(data.password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": user.username,
        "roles": user.roles,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


class UserCreate(BaseModel):
    username: str
    password: str


@app.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    require_admin(current_user)

    existing_user = db.query(User).filter(cast(User.username == user.username, Boolean)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    new_user = User(username=user.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "username": new_user.username}


@app.get("/user_details")
def user_details(current_user: User = Depends(get_current_user)):
    """
    Zwraca dane zalogowanego użytkownika pobrane z payloadu tokena.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "roles": current_user.roles.split(",")
    }


@app.get("/")
def root():
    return {"hello": "world"}


# ================================
# GET ALL

@app.get("/movies")
def get_movies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Movie).all()


@app.get("/links")
def get_links(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Link).all()


@app.get("/ratings")
def get_ratings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Rating).all()


@app.get("/tags")
def get_tags(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Tag).all()


# ================================
# CRUD: MOVIES

@app.post("/movies")
def create_movie(movie: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_movie = Movie(**movie)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")
    return movie


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    for key, value in data.items():
        setattr(movie, key, value)

    db.commit()
    db.refresh(movie)
    return movie


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    movie = db.get(Movie, movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    db.delete(movie)
    db.commit()
    return {"deleted": movie_id}


# ================================
# CRUD: LINKS

@app.post("/links")
def create_link(link: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_link = Link(**link)
    db.add(new_link)
    db.commit()
    db.refresh(new_link)
    return new_link


@app.get("/links/{link_id}")
def get_link(link_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")
    return link


@app.put("/links/{link_id}")
def update_link(link_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")

    for key, value in data.items():
        setattr(link, key, value)

    db.commit()
    db.refresh(link)
    return link


@app.delete("/links/{link_id}")
def delete_link(link_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    link = db.get(Link, link_id)
    if not link:
        raise HTTPException(404, "Link not found")

    db.delete(link)
    db.commit()
    return {"deleted": link_id}


# ================================
# CRUD: RATINGS

@app.post("/ratings")
def create_rating(rating: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_rating = Rating(**rating)
    db.add(new_rating)
    db.commit()
    db.refresh(new_rating)
    return new_rating


@app.get("/ratings/{rating_id}")
def get_rating(rating_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")
    return rating


@app.put("/ratings/{rating_id}")
def update_rating(rating_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")

    for key, value in data.items():
        setattr(rating, key, value)

    db.commit()
    db.refresh(rating)
    return rating


@app.delete("/ratings/{rating_id}")
def delete_rating(rating_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.get(Rating, rating_id)
    if not rating:
        raise HTTPException(404, "Rating not found")

    db.delete(rating)
    db.commit()
    return {"deleted": rating_id}


# ================================
# CRUD: TAGS

@app.post("/tags")
def create_tag(tag: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_tag = Tag(**tag)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag


@app.get("/tags/{tag_id}")
def get_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")
    return tag


@app.put("/tags/{tag_id}")
def update_tag(tag_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")

    for key, value in data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(404, "Tag not found")

    db.delete(tag)
    db.commit()
    return {"deleted": tag_id}
