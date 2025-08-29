from pydantic import BaseModel, EmailStr


class User(BaseModel):
    username: str
    email: EmailStr | None = None
    password: str | None = None
    disabled: bool = False
    role: str = 'employee'


class UserInDB(User):
    hashed_password: str