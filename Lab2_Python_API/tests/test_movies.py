import pytest


@pytest.fixture
def multiple_movies(client, admin_token):
    """Tworzy kilka filmów w bazie i zwraca listę ich danych."""
    movies = [
        {"movieId": 1, "title": "Movie 1", "genres": "Comedy"},
        {"movieId": 2, "title": "Movie 2", "genres": "Action"},
        {"movieId": 3, "title": "Movie 3", "genres": "Drama"},
    ]
    created = []
    for m in movies:
        resp = client.post("/movies", json=m, headers={"Authorization": f"Bearer {admin_token}"})
        created.append(resp.json())
    return created


def test_get_movies_count(client, multiple_movies, admin_token):
    response = client.get("/movies", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(multiple_movies)

    returned_ids = sorted([m["movieId"] for m in data])
    fixture_ids = sorted([m["movieId"] for m in multiple_movies])
    assert returned_ids == fixture_ids


def test_get_movie_by_id(client, admin_token):
    movie = {"movieId": 5, "title": "Matrix", "genres": "Action"}
    post = client.post("/movies", json=movie, headers={"Authorization": f"Bearer {admin_token}"}).json()

    response = client.get(f"/movies/{post['movieId']}", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    assert response.json()["title"] == "Matrix"


def test_get_movies_empty(client, admin_token):
    response = client.get("/movies", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_movie_by_id_not_found(client, admin_token):
    response = client.get("/movies/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404


def test_post_movie(client, admin_token):
    new_movie = {"movieId": 1, "title": "TEST", "genres": "Comedy"}
    response = client.post("/movies", json=new_movie, headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    data = response.json()

    assert data["movieId"] == 1
    assert data["title"] == "TEST"

    get_all = client.get("/movies", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert len(get_all) == 1


def test_put_movie(client, admin_token):
    movie = {"movieId": 7, "title": "Old", "genres": "Sci-fi"}
    created = client.post("/movies", json=movie, headers={"Authorization": f"Bearer {admin_token}"}).json()

    update = {"title": "New Title"}
    response = client.put(f"/movies/{created['movieId']}", json=update, headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


def test_delete_movie(client, admin_token):
    movie = {"movieId": 22, "title": "DeleteMe", "genres": "Drama"}
    created = client.post("/movies", json=movie, headers={"Authorization": f"Bearer {admin_token}"}).json()

    delete = client.delete(f"/movies/{created['movieId']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert delete.status_code == 200

    get = client.get(f"/movies/{created['movieId']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get.status_code == 404
