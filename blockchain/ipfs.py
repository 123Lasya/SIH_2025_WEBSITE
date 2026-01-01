import requests
from django.conf import settings


PINATA_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"


def pin_json_to_ipfs(payload: dict) -> str:
    """
    Send JSON to Pinata, return CID string.
    """
    headers = {
        "Authorization": f"Bearer {settings.PINATA_JWT}",
        "Content-Type": "application/json",
    }

    resp = requests.post(PINATA_URL, headers=headers, json={
        "pinataContent": payload,
        "pinataOptions": {"cidVersion": 1},
    }, timeout=30)

    resp.raise_for_status()
    data = resp.json()
    # Pinata returns IpfsHash
    return data["IpfsHash"]
