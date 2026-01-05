from app.models import User


# ------------------------
# TESTY LOGIN

def test_login_success(client, admin_user):
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    response = client.post("/login", json={"username": "admin", "password": "wrongpass"})
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post("/login", json={"username": "nosuchuser", "password": "xxx"})
    assert response.status_code == 401


# ------------------------
# TESTY TWORZENIA UŻYTKOWNIKA

def test_create_user_admin(client, db_session, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    db_session.query(User).filter(User.username == "newuser").delete()
    db_session.commit()

    response = client.post("/users", json={"username": "newuser", "password": "test123"}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert "ROLE_USER" in data["roles"]


def test_create_user_non_admin(client, db_session, user_token):
    headers = {"Authorization": f"Bearer {user_token}"}

    db_session.query(User).filter(User.username == "failuser").delete()
    db_session.commit()

    response = client.post("/users", json={"username": "failuser", "password": "test123"}, headers=headers)
    assert response.status_code == 403


# ------------------------
# TESTY /user_details

def test_user_details_authorized(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/user_details", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert "ROLE_ADMIN" in data["roles"]


def test_user_details_no_token(client):
    response = client.get("/user_details")
    assert response.status_code in (401, 403)
