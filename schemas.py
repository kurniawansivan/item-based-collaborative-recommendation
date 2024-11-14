from pydantic import BaseModel
from typing import List

class ProductSchema(BaseModel):
    number: str  # Menggunakan number sebagai identifier utama
    name: str
    category: str
    price: float

    class Config:
        orm_mode = True

class ReceiptItemSchema(BaseModel):
    id: int
    receipt_number: str  # Menggunakan number untuk receipt
    product_number: str  # Menggunakan number untuk product
    quantity: int
    gross: float
    net: float
    tax: float

    class Config:
        orm_mode = True

class ReceiptSchema(BaseModel):
    number: str  # Menggunakan number sebagai identifier utama
    booking_time: str
    cancelled: bool
    gross_total: float
    net_total: float
    tax_total: float
    items: List[ReceiptItemSchema] = []

    class Config:
        orm_mode = True

# Schema untuk validasi basket
class BasketRequest(BaseModel):
    basket: List[str]  # List of product numbers
