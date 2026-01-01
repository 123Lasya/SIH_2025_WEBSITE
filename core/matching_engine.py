# core/matching_engine.py

from decimal import Decimal
from farmers.models import FarmerHedge
from buyers.models import BuyerHedge


def run_matching_engine():
    """
    Matches farmer and buyer hedges based on:
    - same crop
    - same end_date
    - same hedge_price

    Allows PARTIAL matching on both sides.
    Uses:
      - quantity
      - matched_quantity
      - status ("OPEN"/"CLOSED")
    """
    # Get all open hedges
    farmers = FarmerHedge.objects.filter(status="OPEN")
    buyers = BuyerHedge.objects.filter(status="OPEN")

    for fh in farmers:
        # Remaining quantity on farmer side
        farmer_remaining = fh.quantity - fh.matched_quantity

        if farmer_remaining <= 0:
            if fh.status != "CLOSED":
                fh.status = "CLOSED"
                fh.save(update_fields=["status"])
            continue

        for bh in buyers:
            # Filter by matching criteria
            if bh.crop != fh.crop:
                continue
            if bh.end_date != fh.end_date:
                continue
            if bh.hedge_price != fh.hedge_price:
                continue

            buyer_remaining = bh.quantity - bh.matched_quantity

            if buyer_remaining <= 0:
                if bh.status != "CLOSED":
                    bh.status = "CLOSED"
                    bh.save(update_fields=["status"])
                continue

            # ---- PARTIAL MATCH LOGIC ----
            match_qty = min(farmer_remaining, buyer_remaining)

            if match_qty <= 0:
                continue

            # Update matched quantities
            fh.matched_quantity += match_qty
            bh.matched_quantity += match_qty

            fh.save(update_fields=["matched_quantity"])
            bh.save(update_fields=["matched_quantity"])

            # Recalculate remaining quantities
            farmer_remaining -= match_qty
            buyer_remaining -= match_qty

            # Close when fully matched
            if farmer_remaining <= 0:
                fh.status = "CLOSED"
                fh.save(update_fields=["status"])
                break  # farmer fully done → move to next farmer

            if buyer_remaining <= 0:
                bh.status = "CLOSED"
                bh.save(update_fields=["status"])
                # continue to next buyer
                continue
