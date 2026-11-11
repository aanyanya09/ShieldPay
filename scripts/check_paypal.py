import os
import httpx
from dotenv import load_dotenv, find_dotenv

path = find_dotenv(usecwd=True)
print("Using .env at:", path or "NOT FOUND")
load_dotenv(path)

cid = os.getenv("PAYPAL_CLIENT_ID")
secret = os.getenv("PAYPAL_SECRET")
print("Client ID found:", bool(cid))
print("Secret found:", bool(secret))
if not cid or not secret:
    raise SystemExit("Fix the names or values in .env and run again.")

r = httpx.post(
    "https://api-m.sandbox.paypal.com/v1/oauth2/token",
    auth=(cid.strip(), secret.strip()),
    data={"grant_type": "client_credentials"},
    timeout=15,
)
print("Status:", r.status_code)
if r.status_code != 200:
    print(r.text[:300])