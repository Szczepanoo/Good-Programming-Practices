from fastapi import FastAPI
import csv
from typing import List

app = FastAPI()

# Klasa modelu danych
class Movie:
    def __init__(self, movieId: int, title: str, genres: str):
        self.movieId = movieId
        self.title = title
        self.genres = genres.split("|")  # zamieniamy "Adventure|Animation" na listę

# Endpoint root
@app.get("/")
def read_root():
    return {"hello": "world"}

# Endpoint /movies
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
