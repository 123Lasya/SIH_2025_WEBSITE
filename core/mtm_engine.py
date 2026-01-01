from decimal import Decimal
from datetime import date

from django.db import transaction

from farmers.models import FarmerHedge
from buyers.models import BuyerHedge
from accounts.models import Wallet
from core.models import MTMHistory
from core.ai_utils import predict_price


def _get_market_price_for_crop(crop: str, today: date, cache: dict) -> Decimal:
    """
    Helper – get today's market price for a crop, using ML model.
    We cache per crop so we don't call predict_price repeatedly.
    """
    if crop not in cache:
        # predict_price may return float/string – wrap safely in Decimal
        price = predict_price(crop, today)
        cache[crop] = Decimal(str(price))
    return cache[crop]


def _apply_pnl_and_log(
    *,
    user,
    hedge_id: int,
    hedge_type: str,  # "FARMER" or "BUYER"
    crop: str,
    quantity: Decimal,
    hedge_price: Decimal,
    market_price: Decimal,
    incremental_pnl: Decimal,
    total_pnl: Decimal,
):
    """
    Apply incremental PnL to user's wallet and create an MTMHistory row.
    """
    wallet: Wallet = user.wallet

    # Apply incremental PnL to wallet balance
    wallet.balance += incremental_pnl
    wallet.save(update_fields=["balance"])

    # Log history row for this hedge + day
    today = date.today()
    MTMHistory.objects.create(
        user=user,
        hedge_id=hedge_id,
        hedge_type=hedge_type,
        crop=crop,
        quantity=quantity,
        hedge_price=hedge_price,
        market_price=market_price,
        pnl=total_pnl,  # store TOTAL PnL as of today
        wallet_balance_after=wallet.balance,
        date=today,
    )


def run_mtm_engine():
    """
    Daily MTM + expiry settlement engine.

    For each OPEN hedge (farmer + buyer):

      1. Fetch today's market price from ML (predict_price).
      2. Compute total MTM PnL:
            Farmer: (hedge_price - market_price) * qty
            Buyer : (market_price - hedge_price) * qty
      3. Work out incremental PnL = total_pnl - last_mtm_pnl
         and apply only that to wallet.balance.
      4. Create MTMHistory row.
      5. If hedge has expired (end_date <= today):
            - Release locked margin
            - Mark hedge as SETTLED
    """
    today = date.today()
    price_cache = {}

    # -----------------------------
    # 1️⃣ FARMER HEDGES
    # -----------------------------
    farmer_hedges = FarmerHedge.objects.filter(status="OPEN")

    for hedge in farmer_hedges:
        with transaction.atomic():
            # Use matched_quantity if present, otherwise total quantity
            qty = hedge.matched_quantity or hedge.quantity
            qty = Decimal(qty)

            # Get today's market price
            market_price = _get_market_price_for_crop(hedge.crop, today, price_cache)
            hedge_price = Decimal(hedge.hedge_price)

            # Farmer PnL = (hedge_price - market_price) * qty
            total_pnl = (hedge_price - market_price) * qty
            last_pnl = hedge.last_mtm_pnl or Decimal("0")
            incremental_pnl = total_pnl - last_pnl

            # Apply PnL + log history
            _apply_pnl_and_log(
                user=hedge.farmer.user,
                hedge_id=hedge.id,
                hedge_type="FARMER",
                crop=hedge.crop,
                quantity=qty,
                hedge_price=hedge_price,
                market_price=market_price,
                incremental_pnl=incremental_pnl,
                total_pnl=total_pnl,
            )

            # Update hedge record
            hedge.last_mtm_pnl = total_pnl

            # 🔚 EXPIRY SETTLEMENT
            if hedge.end_date <= today:
                # Release locked margin ONCE, when we settle
                margin = hedge.margin_amount or Decimal("0")
                if margin > 0:
                    wallet = hedge.farmer.user.wallet
                    # Decrease locked_margin but never go below zero
                    new_locked = wallet.locked_margin - margin
                    if new_locked < 0:
                        new_locked = Decimal("0")
                    wallet.locked_margin = new_locked
                    wallet.save(update_fields=["locked_margin"])

                hedge.status = "SETTLED"

            hedge.save(update_fields=["last_mtm_pnl", "status"])

    # -----------------------------
    # 2️⃣ BUYER HEDGES
    # -----------------------------
    buyer_hedges = BuyerHedge.objects.filter(status="OPEN")

    for hedge in buyer_hedges:
        with transaction.atomic():
            qty = hedge.matched_quantity or hedge.quantity
            qty = Decimal(qty)

            market_price = _get_market_price_for_crop(hedge.crop, today, price_cache)
            hedge_price = Decimal(hedge.hedge_price)

            # Buyer PnL = (market_price - hedge_price) * qty (opposite side)
            total_pnl = (market_price - hedge_price) * qty
            last_pnl = hedge.last_mtm_pnl or Decimal("0")
            incremental_pnl = total_pnl - last_pnl

            _apply_pnl_and_log(
                user=hedge.buyer,
                hedge_id=hedge.id,
                hedge_type="BUYER",
                crop=hedge.crop,
                quantity=qty,
                hedge_price=hedge_price,
                market_price=market_price,
                incremental_pnl=incremental_pnl,
                total_pnl=total_pnl,
            )

            hedge.last_mtm_pnl = total_pnl

            # 🔚 EXPIRY SETTLEMENT
            if hedge.end_date <= today:
                margin = hedge.margin_amount or Decimal("0")
                if margin > 0:
                    wallet = hedge.buyer.wallet
                    new_locked = wallet.locked_margin - margin
                    if new_locked < 0:
                        new_locked = Decimal("0")
                    wallet.locked_margin = new_locked
                    wallet.save(update_fields=["locked_margin"])

                hedge.status = "SETTLED"

            hedge.save(update_fields=["last_mtm_pnl", "status"])

    return "MTM + Expiry Settlement Completed"
