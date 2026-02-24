from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    photo: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    origin: Mapped[int] = mapped_column(Integer, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    profile: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    device: Mapped[int] = mapped_column(Integer, nullable=False)
    api_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
