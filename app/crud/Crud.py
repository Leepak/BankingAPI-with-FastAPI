from sqlalchemy.orm import Session
from app.schemas import Schemas
from app.models.customer import Customer

# CREATE
def create_customer(db: Session, customer_data: Schemas.CustomerCreate):
    db_customer = Customer(
        full_name=customer_data.full_name,
        email=customer_data.email,
        phone_number=customer_data.phone_number,
        address=customer_data.address
    )

    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

# GET ALL
def get_customers(db: Session):
    return db.query(Customer).all()


# GET BY ID
def get_customer(db: Session, customer_id: int):
    return db.query(Customer).filter(Customer.id == customer_id).first()


# UPDATE
def update_customer(db: Session, customer_id: int, updated_data: Schemas.CustomerCreate):
    db_customer = get_customer(db, customer_id)

    if not db_customer:
        return None

    db_customer.full_name = updated_data.full_name
    db_customer.email = updated_data.email
    db_customer.phone_number = updated_data.phone_number
    db_customer.address = updated_data.address

    db.commit()
    db.refresh(db_customer)
    return db_customer


# DELETE
def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)

    if not db_customer:
        return None

    db.delete(db_customer)
    db.commit()
    return db_customer