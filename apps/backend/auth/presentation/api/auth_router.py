"""Auth presentation: API router."""

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from shared.infrastructure.database.session import get_session
from auth.domain.user import User
from auth.infrastructure.user_repository import SQLAlchemyUserRepository
from auth.application.auth_service import AuthService
from auth.presentation.api.schemas import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    UserResponse,
)

router = APIRouter()


def _get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    repo = SQLAlchemyUserRepository(session)
    return AuthService(repo)


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        created_at=user.created_at.isoformat(),
    )


def get_current_user(
    authorization: str = Header(None),
    auth_service: AuthService = Depends(_get_auth_service),
) -> User:
    """Extract and validate JWT from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    try:
        return auth_service.verify_token(parts[1])
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, auth_service: AuthService = Depends(_get_auth_service)):
    try:
        user = auth_service.register(body.username, body.password, body.display_name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    token = auth_service._create_token(user)
    return AuthResponse(token=token, user=_user_to_response(user))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, auth_service: AuthService = Depends(_get_auth_service)):
    try:
        user, token = auth_service.authenticate(body.username, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return AuthResponse(token=token, user=_user_to_response(user))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return _user_to_response(current_user)
