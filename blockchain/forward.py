import datetime
from decimal import Decimal

from web3 import Web3
from django.conf import settings

from blockchain.web3_provider import w3, PRIVATE_KEY, PUBLIC_ADDRESS

# ---------------------------------------------------------
# LOAD ABI
# ---------------------------------------------------------
import json
from pathlib import Path

ABI_PATH = Path(settings.BASE_DIR) / "blockchain" / "abi" / "ForwardSalePOL.json"
with open(ABI_PATH, "r") as f:
    FORWARD_ABI = json.load(f)

FORWARD_CONTRACT = w3.eth.contract(
    address=Web3.to_checksum_address(settings.FORWARD_CONTRACT_ADDRESS),
    abi=FORWARD_ABI
)

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _to_uint_2dec(value):
    """
    Converts Decimal 123.45 → 12345 (scale *100)
    """
    return int(Decimal(value) * 100)

def _date_to_timestamp(d):
    dt = datetime.datetime.combine(d, datetime.time(0, 0))
    dt = dt.replace(tzinfo=datetime.timezone.utc)
    return int(dt.timestamp())


# ---------------------------------------------------------
# AUTO TOKEN APPROVAL
# ---------------------------------------------------------

def approve_tokens(spender, amount):
    """
    Automatically approves POL tokens before calling createContract.
    """
    from blockchain.token import TOKEN_CONTRACT   # import here to avoid circular dep

    scaled = _to_uint_2dec(amount)

    print(f"\n🔄 Approving {scaled} tokens for {spender}...")

    try:
        tx = TOKEN_CONTRACT.functions.approve(
            Web3.to_checksum_address(spender),
            scaled
        ).build_transaction({
            "from": PUBLIC_ADDRESS,
            "nonce": w3.eth.get_transaction_count(PUBLIC_ADDRESS),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

        print("✔ Token Approve TX:", w3.to_hex(tx_hash))
        return True

    except Exception as e:
        print("❌ TOKEN APPROVAL ERROR:", e)
        return False


# ---------------------------------------------------------
# MAIN FUNCTION — CREATE FORWARD CONTRACT
# ---------------------------------------------------------

def create_forward_contract_onchain(contract):
    """
    Create forward contract on chain.
    STRUCT matches ForwardSalePOL.CreateRequest.
    """

    print("\n===== BLOCKCHAIN DEBUG: create_forward_contract_onchain =====")
    try:
        print("Contract ID:", contract.id)
        print("Buyer:", contract.buyer.user.wallet_address if contract.buyer else "None")
        print("Crop:", contract.crop)
        print("Quantity:", contract.quantity)
        print("CID:", contract.ipfs_cid)
        print("Warehouse:", contract.warehouse_id)
        print("Start:", contract.start_date)
        print("End:", contract.end_date)
        print("Pricing:", contract.price_A, contract.price_B, contract.price_C)

        buyer_wallet = contract.buyer.user.wallet_address
        quantity = _to_uint_2dec(contract.quantity)
        start_ts = _date_to_timestamp(contract.start_date)
        end_ts = _date_to_timestamp(contract.end_date)

        # PRICING tuple
        pricing_struct = (
            int(contract.price_A),
            int(contract.price_B),
            int(contract.price_C),
        )

        # MAIN STRUCT (tuple)
        request_struct = (
            Web3.to_checksum_address(buyer_wallet),
            contract.crop,
            contract.ipfs_cid,
            contract.warehouse_id,
            quantity,
            start_ts,
            end_ts,
            pricing_struct
        )

        print("\nSTRUCT WE ARE SENDING TO createContract():")
        print(request_struct)

        # -------------------------------------------------
        # AUTO TOKEN APPROVAL (FOR ESCROW)
        # -------------------------------------------------
        escrow_amount = contract.calculate_escrow_amount()
        approve_tokens(settings.FORWARD_CONTRACT_ADDRESS, escrow_amount)

        # -------------------------------------------------
        # BUILD TRANSACTION
        # -------------------------------------------------
        tx = FORWARD_CONTRACT.functions.createContract(
            request_struct
        ).build_transaction({
            "from": PUBLIC_ADDRESS,
            "nonce": w3.eth.get_transaction_count(PUBLIC_ADDRESS),
            "gas": 900000,
            "gasPrice": w3.eth.gas_price,
        })

        print("TX BUILT")
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        print("TX SIGNED")

        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        print("🔗 FORWARD CONTRACT TX SENT:", w3.to_hex(tx_hash))

        return w3.to_hex(tx_hash)

    except Exception as e:
        print("❌ BLOCKCHAIN ERROR IN create_forward_contract_onchain():", e)
        return None
