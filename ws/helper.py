import jwt
from fastapi import HTTPException, status
from authentication.auth import fake_users_db, SECRET_KEY  # Assuming you're using an in-memory DB
from utils.constants import ALGORITHM

async def get_current_user_from_token(token: str):
    try:
        # Decode the JWT token using the SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")

        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing the username"
            )

        user = fake_users_db.get(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in the database"
            )

        if user.get("disabled"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User is disabled"
            )

        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )