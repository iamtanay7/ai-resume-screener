"""FastAPI dependency injection for authentication and role-based access control."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from server.models.user import UserResponse
from server.services import auth_service, firestore_db

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> UserResponse:
    """Extract and validate JWT, returning the current user."""
    try:
        payload = auth_service.decode_access_token(credentials.credentials)
        user_id: str = payload.get("sub", "")
        role: str = payload.get("role", "")
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_doc = firestore_db.get_user_by_id(user_id)
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return UserResponse(
        id=user_doc["id"],
        name=user_doc["name"],
        email=user_doc["email"],
        role=role,
    )


def require_recruiter(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiters only.",
        )
    return current_user


def require_candidate(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if current_user.role != "candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Candidates only.",
        )
    return current_user
