import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# katalog app/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# jeden poziom wyżej -> katalog Lab2_Python_API
ROOT_DIR = os.path.dirname(BASE_DIR)

# folder 'database' wewnątrz Lab2_Python_API
DB_PATH = os.path.join(ROOT_DIR, "database", "data.db")

print(">>> Using DB:", DB_PATH)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

from . import models

Base.metadata.create_all(bind=engine)

