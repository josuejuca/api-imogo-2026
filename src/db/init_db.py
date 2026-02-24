from src.db.session import Base, engine, ensure_database_exists
from src import models  # noqa: F401


def init_db() -> None:
    ensure_database_exists()
    Base.metadata.create_all(bind=engine)
