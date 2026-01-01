import json
from web3 import Web3
from django.conf import settings

from .web3_provider import w3, PRIVATE_KEY, PUBLIC_ADDRESS

# ---------------- LOAD ERC20 ABI ----------------

with open(settings.BASE_DIR / "blockchain" / "abi" / "POLToken.json") as f:
    TOKEN_ABI = json.load(f)

TOKEN_CONTRACT = w3.eth.contract(
    address=Web3.to_checksum_address(settings.ERC20_TOKEN_ADDRESS),
    abi=TOKEN_ABI
)


# ---------------- CHECK ALLOWANCE ----------------

def check_allowance(spender_address):
    """
    Reads allowance from ERC20:
    allowance(owner, spender)
    """
    return TOKEN_CONTRACT.functions.allowance(
        PUBLIC_ADDRESS,
        Web3.to_checksum_address(spender_address)
    ).call()


# ---------------- APPROVE TOKEN ----------------

def approve_token(spender_address, amount=10**30):
    """
    Approves the platform contract (hedge or forward)
    to spend user tokens.

    amount default = 1e30 (very large, for hackathon)
    """

    spender = Web3.to_checksum_address(spender_address)

    try:
        tx = TOKEN_CONTRACT.functions.approve(
            spender,
            amount
        ).build_transaction({
            "from": PUBLIC_ADDRESS,
            "nonce": w3.eth.get_transaction_count(PUBLIC_ADDRESS),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)

        print("🔗 APPROVE TX SENT:", w3.to_hex(tx_hash))
        return w3.to_hex(tx_hash)

    except Exception as e:
        print("❌ APPROVE ERROR:", e)
        return None


# ---------------- ENSURE APPROVED ----------------

def ensure_approved(spender_address):
    """
    Ensures allowance > 0 before calling createHedge / createContract.
    If 0 → automatically sends approve().
    """

    spender = Web3.to_checksum_address(spender_address)
    allowance = check_allowance(spender)

    print(f"🔍 Allowance for {spender}: {allowance}")

    if allowance > 0:
        print("✔ Already approved — no action needed.")
        return True

    print("⚠ No allowance → sending approve transaction...")
    tx_hash = approve_token(spender)

    return tx_hash is not None
