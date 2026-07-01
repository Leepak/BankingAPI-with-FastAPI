
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from app.models.user import User
from app.models.customer import Customer
from app.schemas.auth_schema import UserCreate
from app.core.security import hash_password, verify_password


def create_user(db: Session, user: UserCreate):
    """
    Create a new user only if the email exists in customers table.
    
    Args:
        db: Database session
        user: User registration data
    
    Returns:
        Created User object
    
    Raises:
        HTTPException: If email not found in customers table
    """
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered as a user"
        )
    
    # 2. Check if customer exists with this email
    customer = db.query(Customer).filter(Customer.email == user.email).first()
    
    # 3. If customer doesn't exist, show error
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found in customer records. Please contact support."
        )
    
    # 4. Check if this customer already has a user account
    existing_user_for_customer = db.query(User).filter(
        User.customer_id == customer.id
    ).first()
    if existing_user_for_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This customer already has a user account"
        )
    
    # 5. Create the user with customer_id
    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        customer_id=customer.id,  # Link to existing customer
        role="CUSTOMER",  # Default role
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate a user.
    
    Args:
        db: Database session
        email: User's email
        password: User's password
    
    Returns:
        User object if authenticated, None otherwise
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user




