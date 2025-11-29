import pytest


@pytest.fixture
def multiple_ratings(client, admin_token):
    """Tworzy kilka ocen w bazie i zwraca listę ich danych."""
    ratings = [
        {"userId": 1, "movieId": 1, "rating": 4.5, "timestamp": 1234567890},
        {"userId": 2, "movieId": 2, "rating": 3.0, "timestamp": 1234567891},
        {"userId": 3, "movieId": 3, "rating": 5.0, "timestamp": 1234567892},
    ]
    created = []
    for r in ratings:
        resp = client.post("/ratings", json=r, headers={"Authorization": f"Bearer {admin_token}"})
        created.append(resp.json())
    return created


def test_get_ratings_count(client, multiple_ratings, admin_token):
    response = client.get("/ratings", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(multiple_ratings)

    returned_ids = sorted([r["id"] for r in data])
    fixture_ids = sorted([r["id"] for r in multiple_ratings])
    assert returned_ids == fixture_ids


def test_get_rating_by_id(client, admin_token):
    rating = {"userId": 5, "movieId": 10, "rating": 4.0, "timestamp": 987654321}
    post = client.post("/ratings", json=rating, headers={"Authorization": f"Bearer {admin_token}"}).json()

    response = client.get(f"/ratings/{post['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["rating"] == 4.0
    assert response.json()["userId"] == 5
    assert response.json()["movieId"] == 10


def test_get_ratings_empty(client, admin_token):
    response = client.get("/ratings", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_rating_by_id_not_found(client, admin_token):
    response = client.get("/ratings/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404


def test_post_rating(client, admin_token):
    new_rating = {"userId": 10, "movieId": 20, "rating": 3.5, "timestamp": 1111111111}
    response = client.post("/ratings", json=new_rating, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    data = response.json()
    assert data["userId"] == 10
    assert data["movieId"] == 20
    assert data["rating"] == 3.5

    get_all = client.get("/ratings", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert len(get_all) == 1


def test_put_rating(client, admin_token):
    rating = {"userId": 7, "movieId": 30, "rating": 2.0, "timestamp": 2222222222}
    created = client.post("/ratings", json=rating, headers={"Authorization": f"Bearer {admin_token}"}).json()

    update = {"rating": 4.5, "timestamp": 3333333333}
    response = client.put(f"/ratings/{created['id']}", json=update, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["rating"] == 4.5
    assert response.json()["timestamp"] == 3333333333


def test_delete_rating(client, admin_token):
    rating = {"userId": 8, "movieId": 40, "rating": 1.5, "timestamp": 4444444444}
    created = client.post("/ratings", json=rating, headers={"Authorization": f"Bearer {admin_token}"}).json()

    delete = client.delete(f"/ratings/{created['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert delete.status_code == 200

    get = client.get(f"/ratings/{created['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get.status_code == 404
