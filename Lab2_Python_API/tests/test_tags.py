import pytest


@pytest.fixture
def multiple_tags(client, admin_token):
    """Tworzy kilka tagów w bazie i zwraca listę ich danych."""
    tags = [
        {"userId": 1, "movieId": 1, "tag": "Comedy", "timestamp": 1234567890},
        {"userId": 2, "movieId": 2, "tag": "Action", "timestamp": 1234567891},
        {"userId": 3, "movieId": 3, "tag": "Drama", "timestamp": 1234567892},
    ]
    created = []
    for t in tags:
        resp = client.post("/tags", json=t, headers={"Authorization": f"Bearer {admin_token}"})
        created.append(resp.json())
    return created


def test_get_tags_count(client, multiple_tags, admin_token):
    response = client.get("/tags", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(multiple_tags)

    returned_ids = sorted([t["id"] for t in data])
    fixture_ids = sorted([t["id"] for t in multiple_tags])
    assert returned_ids == fixture_ids


def test_get_tag_by_id(client, admin_token):
    tag = {"userId": 5, "movieId": 10, "tag": "Thriller", "timestamp": 987654321}
    post = client.post("/tags", json=tag, headers={"Authorization": f"Bearer {admin_token}"}).json()

    response = client.get(f"/tags/{post['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["tag"] == "Thriller"
    assert response.json()["userId"] == 5
    assert response.json()["movieId"] == 10


def test_get_tags_empty(client, admin_token):
    response = client.get("/tags", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_get_tag_by_id_not_found(client, admin_token):
    response = client.get("/tags/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404


def test_post_tag(client, admin_token):
    new_tag = {"userId": 10, "movieId": 20, "tag": "Romance", "timestamp": 1111111111}
    response = client.post("/tags", json=new_tag, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200

    data = response.json()
    assert data["userId"] == 10
    assert data["movieId"] == 20
    assert data["tag"] == "Romance"

    get_all = client.get("/tags", headers={"Authorization": f"Bearer {admin_token}"}).json()
    assert len(get_all) == 1


def test_put_tag(client, admin_token):
    tag = {"userId": 7, "movieId": 30, "tag": "Sci-fi", "timestamp": 2222222222}
    created = client.post("/tags", json=tag, headers={"Authorization": f"Bearer {admin_token}"}).json()

    update = {"tag": "Horror", "timestamp": 3333333333}
    response = client.put(f"/tags/{created['id']}", json=update, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["tag"] == "Horror"
    assert response.json()["timestamp"] == 3333333333


def test_delete_tag(client, admin_token):
    tag = {"userId": 8, "movieId": 40, "tag": "Fantasy", "timestamp": 4444444444}
    created = client.post("/tags", json=tag, headers={"Authorization": f"Bearer {admin_token}"}).json()

    delete = client.delete(f"/tags/{created['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert delete.status_code == 200

    get = client.get(f"/tags/{created['id']}", headers={"Authorization": f"Bearer {admin_token}"})
    assert get.status_code == 404
