import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.dirname(BASE_DIR)

DB_PATH = os.path.join(ROOT_DIR, "database", "data.db")

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    """
    Tworzy tabele i ładuje dane, jeśli baza jest pusta.
    """
    from . import models
    Base.metadata.create_all(bind=engine)

    from sqlalchemy import inspect
    inspector = inspect(engine)

    tables = inspector.get_table_names()
    print(">>> TABLES FOUND:", tables)
    REQUIRED_TABLES = {"movies", "links", "ratings", "tags"}
    print(">>> REQUIRED TABLES:", REQUIRED_TABLES)

    if REQUIRED_TABLES.issubset(set(tables)):
        with SessionLocal() as db:
            count = db.query(models.Movie).count()
            if count > 0:
                print(">>> Database already initialized. Skipping CSV import.")
                return

    print(">>> Importing CSV data...")
    from .load_data import load_all_data
    load_all_data(SessionLocal)
    print(">>> Data import finished.")

