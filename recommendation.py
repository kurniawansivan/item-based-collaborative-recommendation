from sqlalchemy.orm import Session
from collections import defaultdict
from models import ReceiptItem, Recommendation, Product

def generate_recommendations(db: Session):
    """
    Generate item-based collaborative filtering recommendations using product numbers.
    """
    receipts = db.query(ReceiptItem).all()

    # Build co-occurrence matrix using product numbers
    co_occurrence = defaultdict(lambda: defaultdict(int))
    receipt_products = defaultdict(set)

    for item in receipts:
        product = db.query(Product).filter_by(id=item.product_id).first()
        if product:
            receipt_products[item.receipt_id].add(product.number)

    for products in receipt_products.values():
        for product_a in products:
            for product_b in products:
                if product_a != product_b:
                    co_occurrence[product_a][product_b] += 1

    # Save recommendations to the database
    db.query(Recommendation).delete()  # Clear old recommendations
    for product_number, related_products in co_occurrence.items():
        sorted_recommendations = sorted(
            related_products.items(), key=lambda x: -x[1]
        )[:3]  # Top 3 recommendations
        for recommended_number, _ in sorted_recommendations:
            product = db.query(Product).filter_by(number=product_number).first()
            recommended_product = db.query(Product).filter_by(number=recommended_number).first()
            if product and recommended_product:
                recommendation = Recommendation(
                    product_id=product.id,
                    recommended_product_id=recommended_product.id,
                )
                db.add(recommendation)
    db.commit()
