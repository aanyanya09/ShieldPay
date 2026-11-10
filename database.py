"""
database.py - SQLite storage for ShieldPay.
Implements the 7 required tables (§4, B3) and report handling logic (§6, B7).
"""

import os
import sqlite3
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple

DEFAULT_DB_PATH = "shieldpay.db"


def get_db_path(db_path: Optional[str] = None) -> str:
    """Returns configured DB path or default."""
    if db_path is not None:
        return db_path
    return os.getenv("DB_PATH", DEFAULT_DB_PATH)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a thread-safe connection with dictionary-like row access."""
    path = get_db_path(db_path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Creates all 7 tables required by B3:
    1. products: authoritative catalog prices
    2. orders: purchase transactions
    3. assessments: risk evaluation history & jti token tracker
    4. reports: user-submitted seller reports (starts Unverified, expires in 180 days)
    5. brands: verified brand domains for lookalike detection
    6. feedback: post-payment buyer feedback
    7. audit_log: secure event trail
    """
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    -- 1. products table
    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price_cents INTEGER NOT NULL,
        currency TEXT NOT NULL,
        seller_email TEXT NOT NULL
    );

    -- 2. orders table
    CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        paypal_order_id TEXT,
        product_id TEXT NOT NULL,
        amount_cents INTEGER NOT NULL,
        currency TEXT NOT NULL,
        status TEXT NOT NULL, -- CREATED, ASSESSED, CAPTURED, REJECTED
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    );

    -- 3. assessments table
    -- NOTE: Never store raw pasted messages! Only store category breakdown in signals_json.
    CREATE TABLE IF NOT EXISTS assessments (
        assessment_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        rule_version TEXT NOT NULL,
        signals_json TEXT NOT NULL,
        score INTEGER NOT NULL,
        confidence TEXT NOT NULL,
        outcome TEXT NOT NULL,
        user_action TEXT,
        token_jti TEXT,
        jti_used INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    -- 4. reports table
    CREATE TABLE IF NOT EXISTS reports (
        report_id TEXT PRIMARY KEY,
        seller_key TEXT NOT NULL, -- normalized email
        reporter_id TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL, -- Unverified, Confirmed, Disputed, Removed
        weight REAL DEFAULT 1.0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL
    );

    -- 5. brands table
    CREATE TABLE IF NOT EXISTS brands (
        brand_id TEXT PRIMARY KEY,
        brand_name TEXT NOT NULL,
        verified_domain TEXT NOT NULL
    );

    -- 6. feedback table
    CREATE TABLE IF NOT EXISTS feedback (
        feedback_id TEXT PRIMARY KEY,
        order_id TEXT NOT NULL,
        was_scam INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
    );

    -- 7. audit_log table (no secrets or raw messages logged)
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id TEXT PRIMARY KEY,
        event TEXT NOT NULL,
        order_id TEXT,
        detail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


def seed_demo_data(db_path: Optional[str] = None) -> None:
    """Seeds sample catalog, brands, and reports for testing and demo."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # 1. Sample products
    products = [
        ("prod_headphones_101", "Noise-Cancelling Headphones", 4999, "USD", "merchant-orders@goodaudio.com"),
        ("prod_laptop_202", "Refurbished Ultrabook", 39999, "USD", "paypa1-support@gmail.com"), # T6 lookalike
        ("prod_phone_303", "Flagship Smartphone Deal", 25000, "USD", "deals@scam-shop-confirmed.com"), # Confirmed seller
        ("prod_jacket_404", "Winter Parka Coat", 8900, "USD", "sales@suspect-seller.org") # Unverified reports
    ]
    cur.executemany("""
        INSERT OR REPLACE INTO products (product_id, name, price_cents, currency, seller_email)
        VALUES (?, ?, ?, ?, ?)
    """, products)

    # 2. Known brands and verified domains
    brands = [
        ("brand_paypal", "paypal", "paypal.com"),
        ("brand_amazon", "amazon", "amazon.com"),
        ("brand_apple", "apple", "apple.com"),
        ("brand_microsoft", "microsoft", "microsoft.com"),
        ("brand_google", "google", "google.com"),
        ("brand_netflix", "netflix", "netflix.com"),
        ("brand_ebay", "ebay", "ebay.com"),
        ("brand_dhl", "dhl", "dhl.com"),
        ("brand_fedex", "fedex", "fedex.com")
    ]
    cur.executemany("""
        INSERT OR REPLACE INTO brands (brand_id, brand_name, verified_domain)
        VALUES (?, ?, ?)
    """, brands)

    # 3. Seed reports (§4, L5: 1 Confirmed, 2 Unverified, 1 Expired)
    now = datetime.now(timezone.utc)
    future_180_days = now + timedelta(days=180)
    past_200_days = now - timedelta(days=200)

    demo_reports = [
        (
            "rep_seed_confirmed_1",
            "deals@scam-shop-confirmed.com",
            "reporter_user_88",
            "Non-delivery and fake tracking number provided",
            "Confirmed",
            1.0,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            future_180_days.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "rep_seed_unverified_1",
            "sales@suspect-seller.org",
            "reporter_user_12",
            "Demanded payment before providing items",
            "Unverified",
            1.0,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            future_180_days.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "rep_seed_unverified_2",
            "sales@suspect-seller.org",
            "reporter_user_15",
            "Seller stopped replying after payment inquiry",
            "Unverified",
            1.0,
            now.strftime("%Y-%m-%d %H:%M:%S"),
            future_180_days.strftime("%Y-%m-%d %H:%M:%S")
        ),
        (
            "rep_seed_expired_1",
            "expired-seller@test.com",
            "reporter_user_03",
            "Old dispute",
            "Unverified",
            1.0,
            past_200_days.strftime("%Y-%m-%d %H:%M:%S"),
            (past_200_days + timedelta(days=180)).strftime("%Y-%m-%d %H:%M:%S")
        )
    ]

    cur.executemany("""
        INSERT OR REPLACE INTO reports (report_id, seller_key, reporter_id, reason, status, weight, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, demo_reports)

    conn.commit()
    conn.close()


# -------------------------------------------------------------
# Database Queries / Operations
# -------------------------------------------------------------

def get_product(product_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def list_products(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY name ASC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_order(
    order_id: str,
    paypal_order_id: str,
    product_id: str,
    amount_cents: int,
    currency: str,
    status: str = "CREATED",
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO orders (order_id, paypal_order_id, product_id, amount_cents, currency, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (order_id, paypal_order_id, product_id, amount_cents, currency, status))
    conn.commit()
    conn.close()
    return {
        "order_id": order_id,
        "paypal_order_id": paypal_order_id,
        "product_id": product_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "status": status
    }


def get_order(order_id: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_order_status(order_id: str, status: str, db_path: Optional[str] = None) -> None:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
    conn.commit()
    conn.close()


def save_assessment(
    order_id: str,
    rule_version: str,
    signals_json: Dict[str, Any],
    score: int,
    confidence: str,
    outcome: str,
    user_action: Optional[str] = None,
    token_jti: Optional[str] = None,
    db_path: Optional[str] = None
) -> str:
    """Save assessment without saving raw pasted messages (§4, B3)."""
    assessment_id = f"asm_{uuid.uuid4().hex[:12]}"
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO assessments (
            assessment_id, order_id, rule_version, signals_json,
            score, confidence, outcome, user_action, token_jti, jti_used
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    """, (
        assessment_id, order_id, rule_version, json.dumps(signals_json),
        score, confidence, outcome, user_action, token_jti
    ))
    conn.commit()
    conn.close()
    return assessment_id


def get_assessment_by_jti(token_jti: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM assessments WHERE token_jti = ?", (token_jti,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def mark_jti_used(token_jti: str, db_path: Optional[str] = None) -> bool:
    """Atomically mark token_jti as used. Returns True if updated, False if already used (§4, B2)."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        UPDATE assessments
        SET jti_used = 1
        WHERE token_jti = ? AND jti_used = 0
    """, (token_jti,))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def get_active_reports_for_seller(seller_email: str, db_path: Optional[str] = None) -> Tuple[int, int]:
    """
    Returns active (Confirmed, Unverified) reports for seller.
    Expired reports (> 180 days) are ignored (§6, B7).
    """
    clean_seller = seller_email.strip().lower()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT status, COUNT(*) as cnt
        FROM reports
        WHERE seller_key = ?
          AND expires_at > ?
          AND status IN ('Confirmed', 'Unverified')
        GROUP BY status
    """, (clean_seller, now_str))

    rows = cur.fetchall()
    conn.close()

    confirmed = 0
    unverified = 0
    for r in rows:
        if r["status"] == "Confirmed":
            confirmed = r["cnt"]
        elif r["status"] == "Unverified":
            unverified = r["cnt"]
    return confirmed, unverified


def log_audit(event: str, order_id: Optional[str], detail: str, db_path: Optional[str] = None) -> str:
    """Safe audit logging without secrets (§7, B6)."""
    log_id = f"log_{uuid.uuid4().hex[:12]}"
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO audit_log (log_id, event, order_id, detail)
        VALUES (?, ?, ?, ?)
    """, (log_id, event, order_id, detail))
    conn.commit()
    conn.close()
    return log_id
