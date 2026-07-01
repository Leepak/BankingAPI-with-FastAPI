

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth_schema import UserCreate, UserLogin, Token, UserRole
from app.crud.auth_crud import create_user, authenticate_user
from app.core.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

# REGISTER
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    Email must exist in the customers table.
    """
    db_user = create_user(db, user)
    return {
        "message": "User created successfully",
        "user_id": db_user.id,
        "email": db_user.email,
        "customer_id": db_user.customer_id,
        "role": db_user.role.value
    }
# LOGIN - Updated to return user data
@router.post("/login", response_model=Token)
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = authenticate_user(db, user.email, user.password)

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    # Create token with user data
    token_data = {
        "sub": db_user.email,
        "role": db_user.role.value,  # This will be "ADMIN" or "CUSTOMER"
        "user_id": db_user.id,
        "email": db_user.email
    }
    
    token = create_access_token(token_data)

    # Return token AND user data
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": db_user.role,  # This returns the enum
        "user_id": db_user.id,
        "email": db_user.email
    }





