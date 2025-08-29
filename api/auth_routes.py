from typing import Annotated, Any
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from authentication.auth import fake_users_db, get_password_hash, create_access_token, authenticate_user, \
    create_refresh_token, get_current_active_user, SECRET_KEY
from utils.constants import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, MAIN_APP_LOG_FILENAME
from schemas.token import Token
from schemas.user import User
from datetime import timedelta

from utils.utils import create_logger

auth_router = APIRouter()


log_file = MAIN_APP_LOG_FILENAME
logger = create_logger(log_file)
@auth_router.post("/signup")
async def signup(user: User):
    logger.info(f"Signup attempt for username: {user.username}")

    if user.username in fake_users_db:
        logger.warning(f"Username '{user.username}' already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_password = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "password": hashed_password,
        "email": user.email,
        "disabled": user.disabled,
        "role": user.role,
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )

    logger.info(f"User '{user.username}' successfully registered and token generated")

    return {
        "msg": "User successfully registered",
        "access_token": access_token,
        "token_type": "bearer"
    }


@auth_router.post("/login", response_model=Token)
async def login_method(user: User) -> dict[str, str | Any]:
    logger.info(f"Login attempt for username: {user.username}")

    is_authenticated = authenticate_user(fake_users_db, user.username, user.password)
    if not is_authenticated:
        logger.warning(f"Failed login attempt for username: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"username": user.username, "role": user.role})
    logger.info(f"Access token generated for username: {user.username}")

    refresh_token_expires = timedelta(days=7)
    r_token = create_refresh_token(
        data={"username": user.username}, expires_delta=refresh_token_expires
    )

    logger.info(f"Refresh token generated for username: {user.username}")

    response = {
        "access_token": access_token,
        "refresh_token": r_token,
        "token_type": "bearer"
    }

    return response


@auth_router.post("/logout")
async def logout(current_user: Annotated[User, Depends(get_current_active_user)]):
    logger.info(f"User {current_user.username} logged out")

    # Since JWT tokens are stateless, logout should happen client-side by removing the stored token.
    # Optionally, you can maintain a token blacklist in your application.
    return {"msg": "You have been logged out successfully"}


@auth_router.get("/users/me/", response_model=User)
async def read_users_me(
        current_user: Annotated[User, Depends(get_current_active_user)],
):
    logger.info(f"User {current_user.username} requested their profile")
    return current_user


@auth_router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        logger.info("Refresh token request received")
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username is None:
            logger.warning("Invalid refresh token: Username not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.ExpiredSignatureError:
        logger.warning("Refresh token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        logger.error("Invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"username": username}, expires_delta=access_token_expires
    )
    logger.info(f"New access token generated for {username}")

    return {"access_token": new_access_token, "token_type": "bearer"}
