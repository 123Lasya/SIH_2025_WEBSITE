import os
import requests

# ⚠️ For hackathon you can hard-code your JWT,
# but better: put it in environment as PINATA_JWT
PINATA_JWT = os.environ.get(
    "PINATA_JWT",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI5ZWMxNjI0Yy0zNzYxLTRkMzAtYjEwMi0zNDk0NDg3ZTMxOTIiLCJlbWFpbCI6Im00ODI3MTlAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6IjgxYzA2ODA1NzRmMmNkM2I1NjQ5Iiwic2NvcGVkS2V5U2VjcmV0IjoiODc2YTE5MDBiMGUzYzRkOGEzNTEyZjliYmI3ZjhhNTQ5MDAyNzBkYjY3ZDRhNjRjZjQyMmM2OWJhYzFiZmY5ZCIsImV4cCI6MTc5NjM2MjYxN30.PImQmKa4ghM9L0dw21XdpCV6-LRWK-FGUWI4XlP4Yjw"
)

def pin_json_to_ipfs(payload: dict) -> str:
    """
    Sends JSON to Pinata, returns CID string.
    """
    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "Authorization": f"Bearer {PINATA_JWT}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Pinata returns { IpfsHash: "...", PinSize: ..., Timestamp: ... }
    return data["IpfsHash"]
