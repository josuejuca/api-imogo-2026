from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
import pymysql

from src.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def ensure_database_exists() -> None:
    db_url = make_url(settings.database_url)
    if not db_url.drivername.startswith("mysql"):
        return

    database_name = db_url.database
    if not database_name:
        return

    escaped_database_name = database_name.replace("`", "``")
    charset = db_url.query.get("charset", "utf8mb4")

    connection = pymysql.connect(
        host=db_url.host or "localhost",
        port=db_url.port or 3306,
        user=db_url.username,
        password=db_url.password,
        charset=charset,
        autocommit=True,
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{escaped_database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        connection.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
