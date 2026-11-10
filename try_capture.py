import time
import httpx

base = "http://127.0.0.1:8000"

def make_order(product_id):
    r = httpx.post(f"{base}/api/orders", json={"product_id": product_id})
    return r.json()["order_id"]

def assess(order_id):
    r = httpx.post(f"{base}/api/assess", json={"order_id": order_id, "answers": [False, False, False]})
    return r.json()

def capture(order_id, token, confirm=True):
    r = httpx.post(f"{base}/api/capture", json={"order_id": order_id, "token": token, "confirm": confirm})
    return r.status_code, r.text

print("--- A. Normal purchase (Low risk) ---")
oid = make_order("prod_headphones_101")
a = assess(oid)
print("outcome:", a["outcome"])
print("capture:", capture(oid, a["token"]))
print("same token again (AT4, expect 409):", capture(oid, a["token"]))

print("--- B. Suspicious seller (lookalike email) ---")
oid = make_order("prod_laptop_202")
a = assess(oid)
print("outcome:", a["outcome"], "| wait:", a["wait_seconds"])
print("without confirm (expect 400):", capture(oid, a["token"], confirm=False))
print("confirm too early (expect 403):", capture(oid, a["token"]))
time.sleep(a["wait_seconds"] + 1)
print("confirm after the wait (expect 200):", capture(oid, a["token"]))

print("--- C. Confirmed-reported seller (High risk) ---")
oid = make_order("prod_phone_303")
a = assess(oid)
print("outcome:", a["outcome"], "| token:", a["token"])
print("capture with no token (expect 400):", capture(oid, "no-token"))