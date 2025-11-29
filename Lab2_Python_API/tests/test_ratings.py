import pytest


@pytest.fixture
def multiple_ratings(client):
    """Tworzy kilka ocen w bazie i zwraca listę ich danych."""
    ratings = [
        {"userId": 1, "movieId": 1, "rating": 4.5, "timestamp": 1234567890},
        {"userId": 2, "movieId": 2, "rating": 3.0, "timestamp": 1234567891},
        {"userId": 3, "movieId": 3, "rating": 5.0, "timestamp": 1234567892},
    ]
    created = []
    for r in ratings:
        resp = client.post("/ratings", json=r)
        created.append(resp.json())
    return created


def test_get_ratings_count(client, multiple_ratings):
    response = client.get("/ratings")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(multiple_ratings)

    returned_ids = sorted([r["id"] for r in data])
    fixture_ids = sorted([r["id"] for r in multiple_ratings])
    assert returned_ids == fixture_ids


def test_get_rating_by_id(client):
    rating = {"userId": 5, "movieId": 10, "rating": 4.0, "timestamp": 987654321}
    post = client.post("/ratings", json=rating).json()

    response = client.get(f"/ratings/{post['id']}")
    assert response.status_code == 200
    assert response.json()["rating"] == 4.0
    assert response.json()["userId"] == 5
    assert response.json()["movieId"] == 10


def test_get_ratings_empty(client):
    response = client.get("/ratings")
    assert response.status_code == 200
    assert response.json() == []


def test_get_rating_by_id_not_found(client):
    response = client.get("/ratings/99999")
    assert response.status_code == 404


def test_post_rating(client):
    new_rating = {"userId": 10, "movieId": 20, "rating": 3.5, "timestamp": 1111111111}
    response = client.post("/ratings", json=new_rating)
    assert response.status_code == 200

    data = response.json()
    assert data["userId"] == 10
    assert data["movieId"] == 20
    assert data["rating"] == 3.5

    get_all = client.get("/ratings").json()
    assert len(get_all) == 1


def test_put_rating(client):
    rating = {"userId": 7, "movieId": 30, "rating": 2.0, "timestamp": 2222222222}
    created = client.post("/ratings", json=rating).json()

    update = {"rating": 4.5, "timestamp": 3333333333}
    response = client.put(f"/ratings/{created['id']}", json=update)
    assert response.status_code == 200
    assert response.json()["rating"] == 4.5
    assert response.json()["timestamp"] == 3333333333


def test_delete_rating(client):
    rating = {"userId": 8, "movieId": 40, "rating": 1.5, "timestamp": 4444444444}
    created = client.post("/ratings", json=rating).json()

    delete = client.delete(f"/ratings/{created['id']}")
    assert delete.status_code == 200

    get = client.get(f"/ratings/{created['id']}")
    assert get.status_code == 404
