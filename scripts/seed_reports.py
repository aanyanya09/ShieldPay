import os
import sys
from contextlib import closing
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes_extra import get_db, now_utc, ts

BRANDS = ["paypal", "amazon", "apple", "microsoft", "google", "netflix",
          "ebay", "dhl", "fedex", "facebook", "instagram", "walmart"]

now = now_utc()
expires = ts(now + timedelta(days=180))

REPORTS = [
    ("seed_confirmed_1", "deals@scam-shop-confirmed.com", "seed_reporter_a",
     "Demo data: item never delivered.", "Confirmed"),
    ("seed_unverified_1", "gadget-outlet@example.com", "seed_reporter_b",
     "Demo data: asked to pay outside checkout.", "Unverified"),
    ("seed_unverified_2", "gadget-outlet@example.com", "seed_reporter_c",
     "Demo data: urgent pressure to pay.", "Unverified"),
]

with closing(get_db()) as conn:
    for name in BRANDS:
        conn.execute(
            "INSERT OR IGNORE INTO brands (brand_id, brand_name, verified_domain) VALUES (?,?,?)",
            (name, name, f"{name}.com"),
        )
    for rid, key, reporter, reason, status in REPORTS:
        conn.execute(
            "INSERT OR IGNORE INTO reports (report_id, seller_key, reporter_id, reason, status, weight, created_at, expires_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (rid, key, reporter, reason, status, 1.0, ts(now), expires),
        )
    conn.commit()
print("Seeded brands and reports.")