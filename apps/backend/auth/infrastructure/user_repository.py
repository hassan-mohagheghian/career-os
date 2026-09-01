"""Auth infrastructure: SQLAlchemy User repository."""

from sqlalchemy.orm import Session

from auth.domain.user import User
from auth.domain.user_repository import UserRepositoryInterface
from auth.infrastructure.user_model import UserModel


class SQLAlchemyUserRepository(UserRepositoryInterface):
    def __init__(self, session: Session):
        self._session = session

    def _to_domain(self, model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            display_name=model.display_name,
            password_hash=model.password_hash,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, user: User) -> UserModel:
        return UserModel(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            password_hash=user.password_hash,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    def get_by_id(self, user_id: str) -> User | None:
        model = self._session.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_domain(model) if model else None

    def get_by_username(self, username: str) -> User | None:
        model = self._session.query(UserModel).filter(UserModel.username == username).first()
        return self._to_domain(model) if model else None

    def create(self, user: User) -> User:
        model = self._to_model(user)
        self._session.add(model)
        self._session.flush()
        return user

    def update(self, user: User) -> User:
        model = self._session.query(UserModel).filter(UserModel.id == user.id).first()
        if model is None:
            raise ValueError(f"User {user.id} not found")
        model.username = user.username
        model.display_name = user.display_name
        model.password_hash = user.password_hash
        model.updated_at = user.updated_at
        self._session.flush()
        return user

    def delete(self, user_id: str) -> None:
        self._session.query(UserModel).filter(UserModel.id == user_id).delete()
        self._session.flush()
