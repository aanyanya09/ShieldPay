import os
import sys
from contextlib import closing
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routes_extra import get_db, now_utc, ts

now = now_utc()
expires = ts(now + timedelta(days=180))

REPORTS = [
    ("seed_jacket_1", "sales@suspect-seller.org", "seed_reporter_d",
     "Demo data: item never arrived.", "Unverified"),
    ("seed_jacket_2", "sales@suspect-seller.org", "seed_reporter_e",
     "Demo data: asked to pay outside checkout.", "Unverified"),
]

with closing(get_db()) as conn:
    for rid, key, reporter, reason, status in REPORTS:
        conn.execute(
            "INSERT OR IGNORE INTO reports (report_id, seller_key, reporter_id, reason, status, weight, created_at, expires_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (rid, key, reporter, reason, status, 1.0, ts(now), expires),
        )
    conn.commit()
print("Jacket seller reports added.")