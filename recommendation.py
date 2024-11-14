from sqlalchemy.orm import Session
from models import ReceiptItem, Recommendation
from collections import defaultdict

def generate_recommendations(db: Session):
    product_pair_counts = defaultdict(int)
    items = db.query(ReceiptItem).all()
    receipts_products = defaultdict(set)

    # Build receipt-wise product co-occurrence
    for item in items:
        receipts_products[item.receipt_id].add(item.product_id)

    # Count product co-occurrences
    for products in receipts_products.values():
        for product_id in products:
            for other_product_id in products:
                if product_id != other_product_id:
                    product_pair_counts[(product_id, other_product_id)] += 1

    # Generate recommendations based on highest co-occurrence
    recommendations = defaultdict(list)
    for (product_id, other_product_id), count in product_pair_counts.items():
        recommendations[product_id].append((other_product_id, count))

    # Sort recommendations by frequency and limit to top recommendations
    db.query(Recommendation).delete()  # Clear old recommendations
    for product_id, related_products in recommendations.items():
        sorted_products = sorted(related_products, key=lambda x: -x[1])[:5]  # Top 5 recommendations
        for other_product_id, _ in sorted_products:
            recommendation = Recommendation(
                product_id=product_id,
                recommended_product_id=other_product_id
            )
            db.add(recommendation)

    db.commit()
