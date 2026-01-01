from web3 import Web3
from django.conf import settings
import json

# -----------------------------
# WEB3 PROVIDER SETUP
# -----------------------------

w3 = Web3(Web3.HTTPProvider(settings.WEB3_RPC_URL))

if not w3.is_connected():
    raise RuntimeError("Web3 is not connected. Check WEB3_RPC_URL")

CHAIN_ID = 80002  # Polygon Amoy testnet

PUBLIC_ADDRESS = Web3.to_checksum_address(settings.WEB3_PUBLIC_ADDRESS)
PRIVATE_KEY = settings.WEB3_PRIVATE_KEY

# -----------------------------
# ERC20 TOKEN (POL) CONTRACT
# -----------------------------

# Load ERC20 ABI from blockchain/abi/POLToken.json
with open(settings.BASE_DIR / "blockchain" / "abi" / "POLToken.json") as f:
    POL_TOKEN_ABI = json.load(f)

POL_TOKEN_ADDRESS = Web3.to_checksum_address(settings.ERC20_TOKEN_ADDRESS)

TOKEN_CONTRACT = w3.eth.contract(
    address=POL_TOKEN_ADDRESS,
    abi=POL_TOKEN_ABI
)


def send_tx(fn):
    """
    Helper to build, sign & send a transaction for a contract function.
    Usage:
        tx_hash, receipt = send_tx(
            some_contract.functions.someMethod(arg1, arg2)
        )
    """
    nonce = w3.eth.get_transaction_count(PUBLIC_ADDRESS)

    tx = fn.build_transaction(
        {
            "from": PUBLIC_ADDRESS,
            "nonce": nonce,
            "chainId": CHAIN_ID,
            "gas": 600000,
            "gasPrice": w3.eth.gas_price,
        }
    )

    signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_hash.hex(), receipt


def ensure_approved(spender: str, required_amount: int):
    """
    Ensure that `spender` (Hedge or Forward contract) is allowed to
    transfer at least `required_amount` POL tokens from PUBLIC_ADDRESS.

    Safe mode: we approve ONLY the required amount (not infinite).
    """
    if required_amount <= 0:
        # Nothing to approve
        return

    spender = Web3.to_checksum_address(spender)

    current_allowance = TOKEN_CONTRACT.functions.allowance(
        PUBLIC_ADDRESS,
        spender
    ).call()

    if current_allowance >= required_amount:
        print(f"✅ Already approved: {current_allowance} >= {required_amount}")
        return

    print(f"🔄 Approving {required_amount} tokens for {spender}...")

    fn = TOKEN_CONTRACT.functions.approve(spender, required_amount)
    tx_hash, receipt = send_tx(fn)

    print(f"✅ Approve tx hash: {tx_hash}")
    return tx_hash
