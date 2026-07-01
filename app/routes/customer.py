from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import Crud
from app.database import get_db
from app.schemas import Schemas
from app.core.permission import is_admin 
from app.models.user import User


router = APIRouter(prefix="/customers", tags=["Customers"])


# CREATE CUSTOMER
@router.post("/", response_model=Schemas.CustomerResponse)
def create_customer(
    customer: Schemas.CustomerCreate,
      db: Session = Depends(get_db),
      current_user: User = Depends(is_admin)
      ):
    return Crud.create_customer(db, customer)


# GET ALL CUSTOMERS
@router.get("/", response_model=list[Schemas.CustomerResponse])
def get_customers(
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
    
    ):
    return Crud.get_customers(db)


# GET BY ID
@router.get("/{customer_id}", response_model=Schemas.CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    customer = Crud.get_customer(db, customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# UPDATE
@router.put("/{customer_id}", response_model=Schemas.CustomerResponse)
def update_customer(
    customer_id: int,
    customer: Schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    updated = Crud.update_customer(db, customer_id, customer)

    if not updated:
        raise HTTPException(status_code=404, detail="Customer not found")

    return updated


# DELETE
@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int, 
    db: Session = Depends(get_db),
      current_user: User = Depends(is_admin)
      ):
    deleted = Crud.delete_customer(db, customer_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Customer not found")

    return {"message": "Customer deleted successfully"}