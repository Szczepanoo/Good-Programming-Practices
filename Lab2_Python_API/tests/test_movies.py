import pytest


@pytest.fixture
def multiple_movies(client):
    """Tworzy kilka filmów w bazie i zwraca listę ich danych."""
    movies = [
        {"movieId": 1, "title": "Movie 1", "genres": "Comedy"},
        {"movieId": 2, "title": "Movie 2", "genres": "Action"},
        {"movieId": 3, "title": "Movie 3", "genres": "Drama"},
    ]
    created = []
    for m in movies:
        resp = client.post("/movies", json=m)
        created.append(resp.json())
    return created


def test_get_movies_count(client, multiple_movies):
    response = client.get("/movies")
    assert response.status_code == 200

    data = response.json()
    # weryfikujemy, że GET zwraca dokładnie tyle elementów, ile fixtura
    assert len(data) == len(multiple_movies)

    # dodatkowo możemy sprawdzić, że ID/tytuły się zgadzają
    returned_ids = sorted([m["movieId"] for m in data])
    fixture_ids = sorted([m["movieId"] for m in multiple_movies])
    assert returned_ids == fixture_ids


def test_get_movie_by_id(client):
    movie = {"movieId": 5, "title": "Matrix", "genres": "Action"}
    post = client.post("/movies", json=movie).json()

    response = client.get(f"/movies/{post['movieId']}")

    assert response.status_code == 200
    assert response.json()["title"] == "Matrix"


def test_get_movies_empty(client):
    response = client.get("/movies")
    assert response.status_code == 200
    assert response.json() == []


def test_get_movie_by_id_not_found(client):
    response = client.get("/movies/99999")
    assert response.status_code == 404


def test_post_movie(client):
    new_movie = {"movieId": 1, "title": "TEST", "genres": "Comedy"}
    response = client.post("/movies", json=new_movie)

    assert response.status_code == 200
    data = response.json()

    assert data["movieId"] == 1
    assert data["title"] == "TEST"

    get_all = client.get("/movies").json()
    assert len(get_all) == 1


def test_put_movie(client):
    movie = {"movieId": 7, "title": "Old", "genres": "Sci-fi"}
    created = client.post("/movies", json=movie).json()

    update = {"title": "New Title"}
    response = client.put(f"/movies/{created['movieId']}", json=update)

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_delete_movie(client):
    movie = {"movieId": 22, "title": "DeleteMe", "genres": "Drama"}
    created = client.post("/movies", json=movie).json()

    delete = client.delete(f"/movies/{created['movieId']}")
    assert delete.status_code == 200

    get = client.get(f"/movies/{created['movieId']}")
    assert get.status_code == 404
