from sqlalchemy import Column, String, Integer, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    number = Column(String, unique=True, nullable=False)
    category = Column(String)
    price = Column(Float)

class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(String, unique=True, nullable=False)
    booking_time = Column(DateTime)
    cancelled = Column(Boolean, default=False)
    gross_total = Column(Float)
    net_total = Column(Float)
    tax_total = Column(Float)
    items = relationship("ReceiptItem", back_populates="receipt")

class ReceiptItem(Base):
    __tablename__ = "receipt_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(UUID(as_uuid=True), ForeignKey("receipts.id"))
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    quantity = Column(Float)
    gross = Column(Float)
    net = Column(Float)
    tax = Column(Float)

    receipt = relationship("Receipt", back_populates="items")
    product = relationship("Product")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
    recommended_product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"))
