
import enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    CUSTOMER = "CUSTOMER"

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(
        min_length=6,
        max_length=72  
    )

class UserLogin(BaseModel):
    email: EmailStr
    password: str   

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[UserRole] = None  # Add role
    user_id: Optional[int] = None    # Add user ID
    email: Optional[EmailStr] = None # Add email

class TokenData(BaseModel):
    email: str | None = None
    role: str | None = None
    user_id: int | None = None  # Add user_id