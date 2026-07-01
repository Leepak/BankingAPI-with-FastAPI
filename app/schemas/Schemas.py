from pydantic import BaseModel, EmailStr
from typing import Optional


# -------------------
# Create Customer
# -------------------
class CustomerCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    address: Optional[str] = None


# -------------------
# Response Schema
# -------------------
class CustomerResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone_number: Optional[str]
    address: Optional[str]

    class Config:
        from_attributes = True 