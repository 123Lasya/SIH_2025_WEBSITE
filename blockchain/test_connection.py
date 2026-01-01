from blockchain.web3_provider import w3, PUBLIC_ADDRESS

print("Connected:", w3.is_connected())
print("Current Block:", w3.eth.block_number)
print("Platform Wallet:", PUBLIC_ADDRESS)
