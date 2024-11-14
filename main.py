from fastapi import FastAPI, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import Product, Receipt, ReceiptItem, Recommendation
from recommendation import generate_recommendations
from schemas import BasketRequest
import httpx
import os
from dotenv import load_dotenv
import base64
from typing import List
from collections import defaultdict

# Load environment variables
load_dotenv()

app = FastAPI()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database
@app.on_event("startup")
def startup_event():
    init_db()

# Securely access API credentials and URLs
API_BASE_URL = os.getenv("API_BASE_URL")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
API_USERNAME = os.getenv("API_USERNAME")
API_PASSWORD = os.getenv("API_PASSWORD")

# Create the authorization header
credentials = f"{API_USERNAME}:{API_PASSWORD}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
headers = {"Authorization": f"Basic {encoded_credentials}"}

@app.post("/load_products/")
async def load_products(db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/{ACCOUNT_ID}/products", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch products")

        products_data = response.json()["results"]
        for product in products_data:
            existing_product = db.query(Product).filter_by(number=product["number"]).first()
            if existing_product:
                existing_product.name = product["name"]
                existing_product.number = product["number"]
                existing_product.category = product.get("commodityGroup", {}).get("name", "")
                existing_product.price = product.get("prices", [{}])[0].get("value", 0.0)
            else:
                db_product = Product(
                    id=product["id"],
                    name=product["name"],
                    number=product["number"],
                    category=product.get("commodityGroup", {}).get("name", ""),
                    price=product.get("prices", [{}])[0].get("value", 0.0)
                )
                db.add(db_product)
        db.commit()
    return {"message": "Products loaded successfully"}

@app.post("/load_receipts/")
async def load_receipts(db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/{ACCOUNT_ID}/receipts", headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch receipts")

        receipts_data = response.json()["results"]
        for receipt in receipts_data:
            existing_receipt = db.query(Receipt).filter_by(number=receipt["number"]).first()
            if existing_receipt:
                existing_receipt.number = receipt["number"]
                existing_receipt.booking_time = receipt["bookingTime"]
                existing_receipt.cancelled = receipt["cancelled"]
                existing_receipt.gross_total = receipt["total"]["gross"]
                existing_receipt.net_total = receipt["total"]["net"]
                existing_receipt.tax_total = receipt["total"]["tax"]
            else:
                db_receipt = Receipt(
                    id=receipt["id"],
                    number=receipt["number"],
                    booking_time=receipt["bookingTime"],
                    cancelled=receipt["cancelled"],
                    gross_total=receipt["total"]["gross"],
                    net_total=receipt["total"]["net"],
                    tax_total=receipt["total"]["tax"]
                )
                db.add(db_receipt)

            for item in receipt.get("items", []):
                product = db.query(Product).filter_by(id=item["product"]["id"]).first()
                if product:
                    existing_item = db.query(ReceiptItem).filter_by(receipt_id=receipt["id"], product_id=product.id).first()
                    if existing_item:
                        existing_item.quantity = item["quantity"]
                        existing_item.gross = item["total"]["gross"]
                        existing_item.net = item["total"]["net"]
                        existing_item.tax = item["total"]["taxPayments"][0]["amount"]
                    else:
                        db_item = ReceiptItem(
                            receipt_id=receipt["id"],
                            product_id=product.id,
                            quantity=item["quantity"],
                            gross=item["total"]["gross"],
                            net=item["total"]["net"],
                            tax=item["total"]["taxPayments"][0]["amount"]
                        )
                        db.add(db_item)
                    
        db.commit()
    return {"message": "Receipts loaded successfully"}

@app.post("/generate_recommendations/")
def generate_recommendations_endpoint(db: Session = Depends(get_db)):
    generate_recommendations(db)
    return {"message": "Recommendations generated successfully"}

@app.get("/recommendations/{product_number}")
def get_recommendations(product_number: str, db: Session = Depends(get_db)):
    """
    Get recommendations based on product number.
    """
    product = db.query(Product).filter_by(number=product_number).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    recommendations = db.query(Recommendation).filter_by(product_id=product.id).all()
    if not recommendations:
        raise HTTPException(status_code=404, detail="No recommendations found for this product")

    recommended_numbers = [
        db.query(Product).filter_by(id=rec.recommended_product_id).first().number
        for rec in recommendations
    ]
    return {"recommended_products": recommended_numbers}

@app.post("/basket_recommendations/")
def get_basket_recommendations(data: BasketRequest, db: Session = Depends(get_db)):
    """
    Get product recommendations based on items in the basket using product numbers.
    """
    basket_numbers = data.basket
    recommended_numbers = defaultdict(int)

    for number in basket_numbers:
        product = db.query(Product).filter_by(number=number).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product with number {number} not found")
        recommendations = db.query(Recommendation).filter_by(product_id=product.id).all()
        for rec in recommendations:
            recommended_product = db.query(Product).filter_by(id=rec.recommended_product_id).first()
            if recommended_product and recommended_product.number not in basket_numbers:
                recommended_numbers[recommended_product.number] += 1

    # Sort and return the top 3 recommendations
    sorted_recommendations = sorted(recommended_numbers.items(), key=lambda x: -x[1])[:3]
    return {"recommended_products": [number for number, _ in sorted_recommendations]}
