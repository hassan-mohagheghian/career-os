"""Auth infrastructure: SQLAlchemy User model."""

from sqlalchemy import Column, String, DateTime, func

from shared.infrastructure.database.sqlalchemy_config import Base


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id = Column(String(36), primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    display_name = Column(String(128), nullable=False)
    password_hash = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
