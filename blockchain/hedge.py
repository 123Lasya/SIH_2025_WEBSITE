import json
import datetime
from decimal import Decimal

from web3 import Web3
from django.conf import settings

from blockchain.web3_provider import (
    w3,
    PUBLIC_ADDRESS,
    PRIVATE_KEY,
    ensure_approved,
)

# -----------------------------
# LOAD HEDGE CONTRACT
# -----------------------------

with open(settings.BASE_DIR / "blockchain" / "abi" / "HedgeContractPOL.json") as f:
    HEDGE_ABI = json.load(f)

HEDGE_CONTRACT = w3.eth.contract(
    address=Web3.to_checksum_address(settings.HEDGE_CONTRACT_ADDRESS),
    abi=HEDGE_ABI,
)

# -----------------------------
# UTILITIES
# -----------------------------


def _to_uint(value: Decimal) -> int:
    """Convert Decimal to integer without decimals (2 decimal places already handled in DB)."""
    return int(value)


def _date_to_timestamp(d) -> int:
    """Convert Python date to Unix timestamp (00:00 UTC)."""
    if isinstance(d, str):
        # Safeguard: if end_date is a string like "2025-12-31"
        d = datetime.datetime.strptime(d, "%Y-%m-%d").date()

    dt = datetime.datetime.combine(d, datetime.time(0, 0))
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp())


# -----------------------------
# FARMER HEDGE → createHedge
# -----------------------------


def create_farmer_hedge_onchain(hedge):
    print("\n===== BLOCKCHAIN DEBUG: create_farmer_hedge_onchain =====")

    try:
        print("Hedge ID:", hedge.id)
        print("Crop:", hedge.crop)
        print("Quantity:", hedge.quantity)
        print("Hedge Price:", hedge.hedge_price)
        print("End Date:", hedge.end_date)
        print("Margin:", hedge.margin_amount)

        expiry_timestamp = _date_to_timestamp(hedge.end_date)
        print("Expiry → Timestamp:", expiry_timestamp)

        request_struct = {
            "position": 0,
            "crop": str(hedge.crop),
            "quantity": int(hedge.quantity),
            "hedgePrice": int(hedge.hedge_price),
            "expiry": expiry_timestamp,
            "stake": int(hedge.margin_amount),
        }

        print("STRUCT WE ARE SENDING:")
        print(request_struct)

        # ⭐ Try building tx to see if ABI mismatch occurs
        tx = HEDGE_CONTRACT.functions.createHedge(
            request_struct
        ).build_transaction({
            "from": PUBLIC_ADDRESS,
            "nonce": w3.eth.get_transaction_count(PUBLIC_ADDRESS),
            "gas": 700000,
            "gasPrice": w3.eth.gas_price,
        })

        print("TX BUILT SUCCESSFULLY (before signing)")
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        print("TX SIGNED")

        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print("🔗 HEDGE TX SENT:", w3.to_hex(tx_hash))

        return w3.to_hex(tx_hash)

    except Exception as e:
        print("❌ BLOCKCHAIN ERROR IN create_farmer_hedge_onchain():", e)
        return None



# -----------------------------
# BUYER HEDGE → createHedge
# -----------------------------


def create_buyer_hedge_onchain(hedge):
    """
    Sends createHedge(struct) for a buyer.
    Buyer = SHORT = position 1
    Stake = margin_amount (already stored in DB)
    """

    expiry_timestamp = _date_to_timestamp(hedge.end_date)

    quantity_int = _to_uint(hedge.quantity)
    hedge_price_int = _to_uint(hedge.hedge_price)
    stake_int = _to_uint(hedge.margin_amount)

    # 1️⃣ Ensure POL token approval for HedgeContractPOL
    ensure_approved(settings.HEDGE_CONTRACT_ADDRESS, stake_int)

    request_struct = {
        "position": 1,  # SHORT
        "crop": hedge.crop,
        "quantity": quantity_int,
        "hedgePrice": hedge_price_int,
        "expiry": expiry_timestamp,
        "stake": stake_int,
    }

    try:
        tx = HEDGE_CONTRACT.functions.createHedge(
            request_struct
        ).build_transaction(
            {
                "from": PUBLIC_ADDRESS,
                "nonce": w3.eth.get_transaction_count(PUBLIC_ADDRESS),
                "gas": 600000,
                "gasPrice": w3.eth.gas_price,
            }
        )

        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_Transaction)

        print("🔗 BUYER HEDGE TX:", w3.to_hex(tx_hash))
        return w3.to_hex(tx_hash)

    except Exception as e:
        print("❌ BUYER BLOCKCHAIN ERROR:", e)
        return None
