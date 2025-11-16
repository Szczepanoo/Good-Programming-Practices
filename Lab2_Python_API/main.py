from fastapi import FastAPI
import csv
from typing import List

app = FastAPI()

# Modele danych
class Movie:
    def __init__(self, movieId: int, title: str, genres: str):
        self.movieId = movieId
        self.title = title
        self.genres = genres.split("|")

class Link:
    def __init__(self, movieId: int, imdbId: str, tmdbId: str):
        self.movieId = movieId
        self.imdbId = imdbId
        self.tmdbId = tmdbId

class Rating:
    def __init__(self, userId: int, movieId: int, rating: float, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.rating = rating
        self.timestamp = timestamp

class Tag:
    def __init__(self, userId: int, movieId: int, tag: str, timestamp: int):
        self.userId = userId
        self.movieId = movieId
        self.tag = tag
        self.timestamp = timestamp


# Endpointy
@app.get("/")
def read_root():
    return {"hello": "world"}

@app.get("/movies")
def get_movies():
    movies: List[Movie] = []
    # Otwieramy plik CSV
    with open("Lab2_Python_API/database/movies.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            movie = Movie(
                movieId=int(row["movieId"]),
                title=row["title"],
                genres=row["genres"]
            )
            movies.append(movie.__dict__)  # serializacja do dict
    return movies


@app.get("/links")
def get_links():
    links: List[Link] = []
    with open("Lab2_Python_API/database/links.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            link = Link(
                movieId=int(row["movieId"]),
                imdbId=row["imdbId"],
                tmdbId=row["tmdbId"]
            )
            links.append(link.__dict__)
    return links


@app.get("/ratings")
def get_ratings():
    ratings: List[Rating] = []
    with open("Lab2_Python_API/database/ratings.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            rating = Rating(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                rating=float(row["rating"]),
                timestamp=int(row["timestamp"])
            )
            ratings.append(rating.__dict__)
    return ratings

@app.get("/tags")
def get_tags():
    tags: List[Tag] = []
    with open("Lab2_Python_API/database/tags.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            tag = Tag(
                userId=int(row["userId"]),
                movieId=int(row["movieId"]),
                tag=row["tag"],
                timestamp=int(row["timestamp"])
            )
            tags.append(tag.__dict__)
    return tags