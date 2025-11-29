import pytest


@pytest.fixture
def multiple_links(client):
    """Tworzy kilka linków w bazie i zwraca listę ich danych."""
    links = [
        {"movieId": 1, "imdbId": "tt0111161", "tmdbId": "1"},
        {"movieId": 2, "imdbId": "tt0068646", "tmdbId": "2"},
        {"movieId": 3, "imdbId": "tt0071562", "tmdbId": "3"},
    ]
    created = []
    for l in links:
        resp = client.post("/links", json=l)
        created.append(resp.json())
    return created


def test_get_links_count(client, multiple_links):
    response = client.get("/links")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == len(multiple_links)

    returned_ids = sorted([l["movieId"] for l in data])
    fixture_ids = sorted([l["movieId"] for l in multiple_links])
    assert returned_ids == fixture_ids


def test_get_link_by_movieId(client):
    link = {"movieId": 5, "imdbId": "tt0137523", "tmdbId": "5"}
    post = client.post("/links", json=link).json()

    response = client.get(f"/links/{post['movieId']}")
    assert response.status_code == 200
    assert response.json()["imdbId"] == "tt0137523"
    assert response.json()["tmdbId"] == "5"


def test_get_links_empty(client):
    response = client.get("/links")
    assert response.status_code == 200
    assert response.json() == []


def test_get_link_by_id_not_found(client):
    response = client.get("/links/99999")
    assert response.status_code == 404


def test_post_link(client):
    new_link = {"movieId": 10, "imdbId": "tt0110912", "tmdbId": "10"}
    response = client.post("/links", json=new_link)

    assert response.status_code == 200
    data = response.json()

    assert data["movieId"] == 10
    assert data["imdbId"] == "tt0110912"
    assert data["tmdbId"] == "10"

    get_all = client.get("/links").json()
    assert len(get_all) == 1


def test_put_link(client):
    link = {"movieId": 15, "imdbId": "tt0109830", "tmdbId": "15"}
    created = client.post("/links", json=link).json()

    update = {"imdbId": "tt9999999", "tmdbId": "99"}
    response = client.put(f"/links/{created['movieId']}", json=update)
    assert response.status_code == 200
    assert response.json()["imdbId"] == "tt9999999"
    assert response.json()["tmdbId"] == "99"


def test_delete_link(client):
    link = {"movieId": 20, "imdbId": "tt0120737", "tmdbId": "20"}
    created = client.post("/links", json=link).json()

    delete = client.delete(f"/links/{created['movieId']}")
    assert delete.status_code == 200

    get = client.get(f"/links/{created['movieId']}")
    assert get.status_code == 404
