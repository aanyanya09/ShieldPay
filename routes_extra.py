import hashlib
import os
import secrets
import sqlite3
import unicodedata
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from security import rate_limit

router = APIRouter()

import hashlib
import os
import secrets
import unicodedata
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import get_db_connection as get_db
from security import rate_limit

router = APIRouter()

TS_FORMAT = "%Y-%m-%d %H:%M:%S"  # same format as SQLite CURRENT_TIMESTAMP (UTC)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def ts(dt: datetime) -> str:
    return dt.strftime(TS_FORMAT)


# ---------- ID normalisation (B5) ----------
def normalize_email(raw: str) -> str:
    """Lowercase, trim, Gmail dots and +tags removed, reject mixed alphabets."""
    value = raw.strip().lower()
    if len(value) > 254 or value.count("@") != 1:
        raise ValueError("invalid email")
    local, domain = value.split("@")
    if not local or "." not in domain:
        raise ValueError("invalid email")
    scripts = set()
    for ch in value:
        if ch.isalpha():
            scripts.add(unicodedata.name(ch, "UNKNOWN").split()[0])
    if len(scripts) > 1:
        raise ValueError("mixed alphabets")
    if domain in ("gmail.com", "googlemail.com"):
        local = local.split("+")[0].replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def reporter_hash(request: Request) -> str:
    ip = request.client.host if request.client else "unknown"
    salt = os.getenv("TOKEN_SECRET", "")
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()[:16]


def require_admin(x_admin_password: str = Header(default="")) -> None:
    expected = os.getenv("ADMIN_PASSWORD", "")
    if not expected or not secrets.compare_digest(
        x_admin_password.encode(), expected.encode()
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")


# ---------- request models ----------
class ReportIn(BaseModel):
    seller_email: str = Field(max_length=254)
    reason: str = Field(min_length=5, max_length=500)


class FeedbackIn(BaseModel):
    order_id: str = Field(min_length=1, max_length=64)
    was_scam: bool


class StatusChange(BaseModel):
    report_id: str = Field(max_length=64)
    status: Literal["Confirmed", "Disputed", "Removed"]
    reference: Optional[str] = Field(default=None, max_length=100)


# ---------- endpoints ----------
@router.post("/api/reports", dependencies=[Depends(rate_limit("reports", 10, 3600))])
async def submit_report(body: ReportIn, request: Request):
    try:
        key = normalize_email(body.seller_email)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid seller email.")

    rid = reporter_hash(request)
    now = now_utc()
    with closing(get_db()) as conn:
        dup = conn.execute(
            "SELECT 1 FROM reports WHERE reporter_id=? AND seller_key=? "
            "AND created_at>=? AND lower(status)!='removed'",
            (rid, key, ts(now - timedelta(days=30))),
        ).fetchone()
        if dup:
            raise HTTPException(status_code=429, detail="You already reported this seller recently.")
        today = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE reporter_id=? AND created_at>=?",
            (rid, ts(now - timedelta(hours=24))),
        ).fetchone()[0]
        if today >= 5:
            raise HTTPException(status_code=429, detail="Daily report limit reached.")
        conn.execute(
            "INSERT INTO reports (report_id, seller_key, reporter_id, reason, status, weight, created_at, expires_at) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (uuid.uuid4().hex, key, rid, body.reason.strip(), "Unverified", 1.0,
             ts(now), ts(now + timedelta(days=180))),
        )
        conn.commit()
    return {
        "status": "received",
        "report_status": "Unverified",
        "note": "Reports are reviewed. A report is a clue, not proof.",
    }


@router.post("/api/feedback", dependencies=[Depends(rate_limit("feedback", 20, 3600))])
async def submit_feedback(body: FeedbackIn):
    with closing(get_db()) as conn:
        exists = conn.execute(
            "SELECT 1 FROM orders WHERE order_id=?", (body.order_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Order not found.")
        conn.execute(
            "INSERT INTO feedback (feedback_id, order_id, was_scam, created_at) VALUES (?,?,?,?)",
            (uuid.uuid4().hex, body.order_id, int(body.was_scam), ts(now_utc())),
        )
        conn.commit()
    return {"status": "thanks"}


@router.get("/api/admin/reports", dependencies=[Depends(require_admin)])
async def admin_list_reports():
    with closing(get_db()) as conn:
        rows = conn.execute(
            "SELECT report_id, seller_key, reason, status, created_at, expires_at "
            "FROM reports ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    return [dict(r) for r in rows]


@router.post("/api/admin/reports", dependencies=[Depends(require_admin)])
async def admin_change_status(body: StatusChange):
    with closing(get_db()) as conn:
        row = conn.execute(
            "SELECT seller_key FROM reports WHERE report_id=?", (body.report_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Report not found.")
        if body.status == "Confirmed":
            distinct = conn.execute(
                "SELECT COUNT(DISTINCT reporter_id) FROM reports "
                "WHERE seller_key=? AND lower(status)!='removed' AND expires_at>=?",
                (row["seller_key"], ts(now_utc())),
            ).fetchone()[0]
            if distinct < 2 and not (body.reference and body.reference.strip()):
                raise HTTPException(
                    status_code=400,
                    detail="Confirm needs 2 different reporters or a complaint reference number.",
                )
        conn.execute(
            "UPDATE reports SET status=? WHERE report_id=?", (body.status, body.report_id)
        )
        conn.commit()
    return {"report_id": body.report_id, "status": body.status}