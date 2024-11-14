from pydantic import BaseModel
from typing import List

class ProductSchema(BaseModel):
    id: str
    name: str
    number: str
    category: str
    price: float

    class Config:
        orm_mode = True

class ReceiptItemSchema(BaseModel):
    id: int
    receipt_id: str
    product_id: str
    quantity: int
    gross: float
    net: float
    tax: float

    class Config:
        orm_mode = True

class ReceiptSchema(BaseModel):
    id: str
    number: str
    booking_time: str
    cancelled: str
    gross_total: float
    net_total: float
    tax_total: float
    items: List[ReceiptItemSchema] = []

    class Config:
        orm_mode = True

# Schema untuk validasi basket
class BasketRequest(BaseModel):
    basket: List[str]
