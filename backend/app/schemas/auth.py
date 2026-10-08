from typing import Literal
from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator


class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120, validation_alias=AliasChoices("name", "full_name"))
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Literal["farmer", "doctor"] = "farmer"
    registration_number: str | None = Field(default=None, max_length=100)
    specialization: str | None = Field(default=None, max_length=160)

    @field_validator("password")
    @classmethod
    def password_has_letters_and_numbers(cls, value: str) -> str:
        if not any(char.isalpha() for char in value) or not any(char.isdigit() for char in value):
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["farmer", "doctor", "admin"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int | None = None
    user: UserRead
