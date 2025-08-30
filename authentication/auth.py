import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta, timezone

from utils.constants import AUTH_LOG_FILENAME, ALGORITHM, REFRESH_TOKEN_EXPIRY
from schemas.token import TokenData
from schemas.user import UserInDB, User
from utils.utils import create_logger

load_dotenv()

# Set up logging
log_file = AUTH_LOG_FILENAME
logger = create_logger(log_file)

# Config
SECRET_KEY = os.getenv('SECRET_KEY')



# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
bearer_scheme = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

fake_users = {}
fake_users_db = {}


def verify_password(plain_password, hashed_password):
    """
    Verifies if the plain password matches the hashed password.

    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Generates a hashed version of the password.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


def get_user(db, username: str):
    """
    Retrieves a user from the database by username.

    Args:
        db: The database dictionary containing user data.
        username: The username to look up.

    Returns:
        The user data if found, None otherwise.
    """
    logger.info(f"Fetching user: {username}")
    if username in db:
        user_dict = db[username]
        # Ensure the `hashed_password` is passed in UserInDB object
        logger.info(f"User {username} found.")
        return user_dict  # This will map the stored data correctly to UserInDB
    logger.warning(f"User {username} not found.")
    return None


def authenticate_user(fake_db, username: str, password: str):
    """
    Authenticates a user against the database.

    Args:
        fake_db: The fake database dictionary.
        username: The username to authenticate.
        password: The password to verify.

    Returns:
        The user data if authenticated, False otherwise.
    """
    logger.info(f"Authenticating user: {username}")
    user = get_user(fake_db, username)
    if not user:
        logger.warning(f"Failed authentication for {username}: User not found.")
        return False
    if not verify_password(password, user['password']):
        logger.warning(f"Failed authentication for {username}: Incorrect password.")
        return False
    logger.info(f"User {username} authenticated successfully.")
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT access token.

    Args:
        data:-пол: The data to encode in the token.
        expires_delta: Optional expiration delta (default 15 minutes).

    Returns:
        The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Access token created for {data['username']} with expiration {expire}.")
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT refresh token.

    Args:
        data: The data to encode in the token.
        expires_delta: Optional expiration delta (default 7 days).

    Returns:
        The encoded JWT refresh token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRY)  # Refresh token expiry (7 days for example)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    logger.info(f"Refresh token created for {data['username']} with expiration {expire}.")
    return encoded_jwt


def decode_token(token: str):
    """
    Decodes and validates a JWT token.

    Args:
        token: The JWT token to decode.

    Returns:
        The decoded payload.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        logger.info("Decoding token.")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token decoded successfully.")
        return payload
    except jwt.InvalidTokenError:
        logger.error("Invalid or expired token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    """
    Retrieves the current user from the JWT token in credentials.

    Args:
        credentials: The HTTP authorization credentials.

    Returns:
        The user data.

    Raises:
        HTTPException: If the token is invalid or user is not found/disabled.
    """
    logger.info("Fetching current user from token.")
    token = credentials.credentials
    data = decode_token(token)
    username = data.get("username")
    if not username:
        logger.error("Token payload does not contain a username.")
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = get_user(fake_users_db, username)
    if not user or user.get("disabled"):
        logger.warning(f"User {username} is inactive or not found.")
        raise HTTPException(status_code=401, detail="User inactive or not found")
    logger.info(f"User {username} is active.")
    return user


async def get_current_active_user(
        current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Ensures the current user is active.

    Args:
        current_user: The current user data.

    Returns:
        The user data if active.

    Raises:
        HTTPException: If the user is inactive.
    """
    logger.info(f"Checking if user {current_user['username']} is active.")
    if current_user['disabled']:
        logger.warning(f"User {current_user['username']} is disabled.")
        raise HTTPException(status_code=400, detail="Inactive user")
    logger.info(f"User {current_user['username']} is active.")
    return current_user
