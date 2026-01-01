from web3 import Web3
from django.conf import settings
from blockchain.web3_provider import w3, send_tx
import json
TOKEN_ABI = json.load(open("blockchain/abi/POLToken.json"))

token_contract = w3.eth.contract(
    address=Web3.to_checksum_address(settings.ERC20_TOKEN_ADDRESS),
    abi=TOKEN_ABI
)

def ensure_approved(spender, amount):
    allowance = token_contract.functions.allowance(
        settings.PUBLIC_ADDRESS,
        spender
    ).call()

    if allowance < amount:
        tx = token_contract.functions.approve(
            spender, int(1e30)   # huge max approval
        )
        tx_hash, receipt = send_tx(tx)
        return tx_hash
