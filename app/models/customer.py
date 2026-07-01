

from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String(255), nullable=False)

    email = Column(String(255), unique=True, index=True, nullable=False)

    phone_number = Column(String(20), unique=True, index=True, nullable=False)

    address = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    accounts = relationship("Account", back_populates="customer")
    
    # Add the reverse relationship to User
    # This allows accessing customer.user to get the user who owns this customer profile
    user = relationship("User", back_populates="customer", uselist=False)

    def __repr__(self):
        return f"<Customer(id={self.id}, email='{self.email}', name='{self.full_name}')>"