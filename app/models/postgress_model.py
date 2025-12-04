from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Enum, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid

from app.config.firebase import Base

# Enums
class UserRole(str, enum.Enum):
    ADMIN = "admin"
    EMPLOYEE = "employee"
    MANAGER = "manager"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50))
    role = Column(Enum(UserRole), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = relationship("Order", back_populates="customer")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    icon = Column(String(255))
    image_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = relationship("Order", back_populates="service")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = Column(String(50), unique=True, index=True, nullable=False)
    customer_id = Column(String, ForeignKey("customers.id"), nullable=False)
    service_id = Column(String, ForeignKey("services.id"), nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    color = Column(String(100))
    unit_price = Column(Float)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    progress_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    customer = relationship("Customer", back_populates="orders")
    service = relationship("Service", back_populates="orders")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(50))
    job_title = Column(String(255), nullable=False)  # ✅ Fixed - removed comma
    referee = Column(String(255))
    bio = Column(Text)
    department = Column(String(255))
    hire_date = Column(DateTime)
    image_url = Column(String(255))
    salary = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    is_read = Column(Boolean, default=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class ExpenseType(str, enum.Enum):
    MATERIAL = "material"
    LABOR = "labor"
    SHIPPING = "shipping"
    UTILITIES = "utilities"
    MARKETING = "marketing"
    MAINTENANCE = "maintenance"
    OTHER = "other"

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime)
    amount = Column(Float, nullable=False)
    type = Column(Enum(ExpenseType), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class News(Base):
    __tablename__ = "news"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    from_date = Column(DateTime, nullable=False)
    to_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

