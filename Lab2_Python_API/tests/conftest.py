import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base, SessionLocal
from app.main import app, get_db, SECRET_KEY, ALGORITHM
from app.models import User
import bcrypt
import jwt
from datetime import datetime, timedelta, UTC

TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///./tests/test.db"

engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def init_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Zwraca sesję DB dla testów; po teście rollback, czyszczenie."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Zwraca TestClient, z override zależności get_db → testowa sesja."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(db_session):
    username = "testadmin"
    db_session.query(User).filter(User.username == username).delete()
    password = "test123"
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(username=username, hashed_password=hashed, roles="ROLE_ADMIN")
    db_session.add(user)
    db_session.commit()

    payload = {
        "sub": user.username,
        "roles": user.roles,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(hours=1)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    db_session.close()

    return token
