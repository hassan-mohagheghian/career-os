"""Auth application: authentication service."""

from __future__ import annotations

from datetime import datetime, timedelta, UTC

import bcrypt
import jwt

from shared.infrastructure.config.app_config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
)
from auth.domain.user import User
from auth.domain.user_repository import UserRepositoryInterface


class AuthService:
    """Handles registration, login, and JWT token management."""

    def __init__(self, user_repo: UserRepositoryInterface):
        self._user_repo = user_repo

    def register(self, username: str, password: str, display_name: str) -> User:
        """Register a new user. Raises ValueError if username taken."""
        existing = self._user_repo.get_by_username(username)
        if existing is not None:
            raise ValueError(f"Username '{username}' is already taken")
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User(username=username, display_name=display_name, password_hash=password_hash)
        return self._user_repo.create(user)

    def authenticate(self, username: str, password: str) -> tuple[User, str]:
        """Authenticate and return (user, jwt_token). Raises ValueError on failure."""
        user = self._user_repo.get_by_username(username)
        if user is None:
            raise ValueError("Invalid username or password")
        if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise ValueError("Invalid username or password")
        token = self._create_token(user)
        return user, token

    def verify_token(self, token: str) -> User:
        """Decode JWT and return the user. Raises ValueError on invalid/expired token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Invalid token payload")
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        return user

    def _create_token(self, user: User) -> str:
        payload = {
            "sub": user.id,
            "username": user.username,
            "exp": datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    def seed_default_user(self) -> User | None:
        """Create the default user from env vars if it doesn't exist."""
        from shared.infrastructure.config.app_config import (
            DEFAULT_USER_USERNAME,
            DEFAULT_USER_PASSWORD,
            DEFAULT_USER_DISPLAY_NAME,
        )
        existing = self._user_repo.get_by_username(DEFAULT_USER_USERNAME)
        if existing is not None:
            return existing
        return self.register(DEFAULT_USER_USERNAME, DEFAULT_USER_PASSWORD, DEFAULT_USER_DISPLAY_NAME)
