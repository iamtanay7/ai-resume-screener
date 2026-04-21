"""Authentication endpoints — signup, login, me."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from server.dependencies import get_current_user
from server.models.user import TokenResponse, UserLoginRequest, UserResponse, UserSignupRequest
from server.services import auth_service, firestore_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: UserSignupRequest) -> TokenResponse:
    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters.",
        )
    if not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required.",
        )

    existing = firestore_db.get_user_by_email(str(payload.email))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_id = str(uuid.uuid4())
    hashed = auth_service.hash_password(payload.password)
    firestore_db.write_user(
        user_id=user_id,
        name=payload.name.strip(),
        email=str(payload.email),
        hashed_password=hashed,
        role=payload.role,
    )

    token = auth_service.create_access_token(user_id=user_id, role=payload.role)
    user = UserResponse(id=user_id, name=payload.name.strip(), email=str(payload.email), role=payload.role)
    logger.info("New %s account created: %s", payload.role, user_id)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest) -> TokenResponse:
    user_doc = firestore_db.get_user_by_email(str(payload.email))
    if user_doc is None or not auth_service.verify_password(payload.password, user_doc["hashedPassword"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    token = auth_service.create_access_token(user_id=user_doc["id"], role=user_doc["role"])
    user = UserResponse(
        id=user_doc["id"],
        name=user_doc["name"],
        email=user_doc["email"],
        role=user_doc["role"],
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    return current_user
