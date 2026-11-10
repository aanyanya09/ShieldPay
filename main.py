"""
main.py - ShieldPay Backend API (§4, B1, B2, B3).
Pre-capture risk assessment and PayPal sandbox checkout gate.
"""
import time
import os
import uuid
import re
import secrets
import logging
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

import database as db
from rules import (
    RULE_VERSION,
    DEFAULT_WAIT_SECONDS,
    SCAM_QUESTIONS,
    ALLOWED_CATEGORIES,
    normalize_seller_id,
    check_brand_lookalike,
    calculate_score,
    determine_confidence,
    determine_outcome
)
from token_service import (
    generate_capture_token,
    verify_capture_token,
    TokenExpiredError,
    TokenInvalidError,
)
from paypal_client import PayPalClient
from security import rate_limit

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("shieldpay")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes and seeds the database when the server starts."""
    db_path = os.getenv("DB_PATH", db.DEFAULT_DB_PATH)
    logger.info("Initializing ShieldPay database at %s", db_path)
    db.init_db(db_path)
    db.seed_demo_data(db_path)
    yield


app = FastAPI(
    title="ShieldPay Backend API",
    description="Pre-capture risk assessment and PayPal sandbox checkout gate.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_BODY_BYTES = 10_000


@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_BODY_BYTES:
        return JSONResponse(status_code=413, content={"detail": "Request too large."})
    return await call_next(request)

paypal_client = PayPalClient()


_runtime_secret = None

def get_token_secret() -> str:
    """Use TOKEN_SECRET from .env. If missing, make a random one for this run only."""
    global _runtime_secret
    secret = os.getenv("TOKEN_SECRET", "")
    if len(secret.encode("utf-8")) >= 32:
        return secret
    if _runtime_secret is None:
        _runtime_secret = secrets.token_hex(32)
        logger.warning("TOKEN_SECRET not set or too short; using a random secret for this run only.")
    return _runtime_secret


# -------------------------------------------------------------
# Request Schemas
# -------------------------------------------------------------

class OrderCreateRequest(BaseModel):
    product_id: str = Field(..., description="The ID of the product from our database catalog")


class AssessRequest(BaseModel):
    order_id: str = Field(..., description="The order ID created in Step 1")
    message: Optional[str] = Field(None, max_length=2000, description="Optional pasted seller message")
    answers: Optional[List[bool]] = Field(default=None, min_length=3, max_length=3, description="Answers to the 3 scam questions. Leave out if skipped.")
    re_answer: Optional[bool] = Field(default=False, description="One-time re-answer attempt if buyer made a mistake (L4)")

class CaptureRequest(BaseModel):
    order_id: str = Field(..., description="The order being paid")
    token: str = Field(..., max_length=2000, description="Signed token from /api/assess")
    confirm: bool = Field(default=False, description="Buyer pressed Confirm")


# -------------------------------------------------------------
# Scam Wording Detector (§5, B4)
# -------------------------------------------------------------

def analyze_message_categories(text: str) -> List[str]:
    """Detect scam wording categories in message text (§5, B4)."""
    if not text:
        return []
    lower = text.lower()
    categories = []

    if re.search(r"\b(urgent|immediately|act now|hurry|within (\d+) (minute|hour)|limited time)\b", lower):
        categories.append("urgency")
    if re.search(r"\b(arrest|police|court|legal action|warrant|penalty|fine|customs)\b", lower):
        categories.append("threat")
    if re.search(r"\b(support|helpdesk|security team|paypal department|account locked|verify your identity)\b", lower):
        categories.append("fake_support")
    if re.search(r"\b(password|pin|otp|code|card number|ssn|cvv)\b", lower):
        categories.append("credential_request")
    if re.search(r"\b(winner|prize|lottery|reward|claim your (refund|fund)|investment return|deposit to receive)\b", lower):
        categories.append("advance_fee")
    if re.search(r"\b(pay outside|direct transfer|friends and family|wire|gift card|crypto|off-platform)\b", lower):
        categories.append("pay_outside_checkout")
    if re.search(r"\b(overpaid|extra money|refunded by mistake|send back the difference)\b", lower):
        categories.append("odd_refund")

    return categories


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "ShieldPay API",
        "paypal_mode": paypal_client.mode
    }


@app.get("/api/products")
async def list_products():
    products = db.list_products()
    return {"products": products}


@app.post("/api/orders", status_code=status.HTTP_201_CREATED, dependencies=[Depends(rate_limit("orders", 30, 3600))])
async def create_order(payload: OrderCreateRequest):
    """
    Step 1: Order Creation (§4, B1).
    Reads authoritative price directly from server database products table.
    """
    product = db.get_product(payload.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{payload.product_id}' not found in database."
        )

    order_id = f"ord_{uuid.uuid4().hex[:12]}"

    try:
        paypal_order = await paypal_client.create_order(
            order_id=order_id,
            amount_cents=product["price_cents"],
            currency=product["currency"],
            description=product["name"],
            seller_email=product["seller_email"]
        )
    except Exception as e:
        logger.error("PayPal order creation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create PayPal order: {str(e)}"
        )

    paypal_order_id = paypal_order.get("id", f"SANDBOX_ORDER_{order_id}")

    db.create_order(
        order_id=order_id,
        paypal_order_id=paypal_order_id,
        product_id=product["product_id"],
        amount_cents=product["price_cents"],
        currency=product["currency"],
        status="CREATED"
    )

    db.log_audit("ORDER_CREATED", order_id, f"Product {product['product_id']}, Amount: {product['price_cents']}")

    return {
        "order_id": order_id,
        "paypal_order_id": paypal_order_id,
        "product_id": product["product_id"],
        "product_name": product["name"],
        "amount_cents": product["price_cents"],
        "currency": product["currency"],
        "seller_email": product["seller_email"],
        "status": "CREATED"
    }


@app.post("/api/assess", dependencies=[Depends(rate_limit("assess", 20, 3600))])
async def assess_risk(payload: AssessRequest):
    """
    Step 3 & 4: Pre-Capture Risk Assessment (§4, B1, §3).
    Evaluates:
      1. Seller reports (Confirmed = 60 pts, Unverified = 20 pts)
      2. Brand lookalike email (40 pts)
      3. The 3 Scam questions (50 pts each)
      4. Message text categories (10 pts each, max 30)
    Applies the soft signal cap (max 49 pts).
    If capture is allowed, issues a signed single-use 5-minute token (§4, B2).
    """
    order = db.get_order(payload.order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    product = db.get_product(order["product_id"])
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product associated with order not found.")

    seller_email = product["seller_email"]
    norm_seller = normalize_seller_id(seller_email)

    reasons: List[str] = []
    not_checked: List[str] = []

    # 1. Report check (§4, L5, §6, B7)
    confirmed_reports, unverified_reports = db.get_active_reports_for_seller(norm_seller)
    report_hit = (confirmed_reports > 0 or unverified_reports > 0)
    if confirmed_reports > 0:
        reasons.append("This seller has been reported by a user, and the report was reviewed.")
    elif unverified_reports > 0:
        reasons.append("This seller has been reported by a user. The report is not yet reviewed.")

    # 2. Brand lookalike check (§6, B5)
    is_lookalike, matched_brand, lookalike_warning = check_brand_lookalike(seller_email)
    brand_hit = is_lookalike
    if is_lookalike and lookalike_warning:
        reasons.append(lookalike_warning)

    # 3. Scam questions check (§3, L6)
    questions_answered = payload.answers is not None
    answers = payload.answers or [False, False, False]
    scam_q_yes = any(answers)

    for idx, ans in enumerate(answers[:3]):
        if ans:
            reasons.append(SCAM_QUESTIONS[idx]["explanation"])

    if not questions_answered:
        not_checked.append("Buyer scam questions were not answered.")

    # 4. Message check (§5, B4)
    message = payload.message or ""
    has_message = bool(message.strip())
    scam_categories = []
    if has_message:
        scam_categories = analyze_message_categories(message)
        for cat in scam_categories:
            exp = ALLOWED_CATEGORIES.get(cat)
            if exp and exp not in reasons:
                reasons.append(exp)
    else:
        not_checked.append("No conversation message provided for text analysis.")

    # 5. Score calculation with soft cap at 49 (§3, L1)
    score, signals_breakdown = calculate_score(
        confirmed_reports=confirmed_reports,
        scam_question_yes=scam_q_yes,
        unverified_reports=unverified_reports,
        is_brand_lookalike=is_lookalike,
        scam_wording_categories=scam_categories
    )

    # 6. Confidence determination (§3, L2)
    confidence = determine_confidence(
        order_checked=True,
        message_checked=has_message,
        questions_answered=questions_answered,
        brand_or_report_hit=(report_hit or brand_hit),
        confirmed_report_found=(confirmed_reports > 0)
    )

    # 7. Outcome determination (§3, L2, L3)
    outcome, action = determine_outcome(score, confidence)

    # One mistaken "Yes" re-answer rule (§3, L4)
    # A single mistaken "Yes" allows one re-answer; confirmed report does not.
    can_reanswer = (outcome == "High risk" and scam_q_yes and confirmed_reports == 0 and not payload.re_answer)

    # Issue signed capture token if allowed (§4, B2)
    # Low risk, Suspicious, Unknown get tokens. High risk does NOT!
    token = None
    token_jti = None
    wait_seconds = int(os.getenv("WAIT_SECONDS", str(DEFAULT_WAIT_SECONDS)))

    secret = get_token_secret()
    if outcome != "High risk":
        token, token_jti, exp = generate_capture_token(
            order_id=order["order_id"],
            amount_cents=order["amount_cents"],
            currency=order["currency"],
            seller_email=seller_email,
            outcome=outcome,
            secret=secret,
            ttl_seconds=300 # 5 minutes
        )

    # Save assessment in DB without raw message (§4, B3)
    user_action = "RE_ANSWERED" if payload.re_answer else "INITIAL"
    assessment_id = db.save_assessment(
        order_id=order["order_id"],
        rule_version=RULE_VERSION,
        signals_json=signals_breakdown,
        score=score,
        confidence=confidence,
        outcome=outcome,
        user_action=user_action,
        token_jti=token_jti
    )

    db.update_order_status(order["order_id"], "ASSESSED")
    db.log_audit("ASSESSMENT_COMPLETED", order["order_id"], f"Score: {score}, Confidence: {confidence}, Outcome: {outcome}")

    return {
        "assessment_id": assessment_id,
        "order_id": order["order_id"],
        "score": score,
        "confidence": confidence,
        "outcome": outcome,
        "action": action,
        "reasons": reasons,
        "not_checked": not_checked,
        "wait_seconds": wait_seconds if outcome == "Suspicious" else 0,
        "can_reanswer": can_reanswer,
        "token": token
    }

@app.post("/api/capture", dependencies=[Depends(rate_limit("capture", 20, 3600))])
async def capture_payment(payload: CaptureRequest):
    """Capture gate (B2). Money moves only if every check passes."""

    # Check 1: the order exists and is ready to be paid
    order = db.get_order(payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found.")
    if order["status"] == "CAPTURED":
        raise HTTPException(status_code=409, detail="This order was already paid.")
    if order["status"] != "ASSESSED":
        raise HTTPException(status_code=400, detail="Run the safety check before paying.")

    # Check 2: the token is genuine and not expired
    try:
        claims = verify_capture_token(payload.token, get_token_secret())
    except TokenExpiredError:
        raise HTTPException(status_code=410, detail="The check has expired. Please run it again.")
    except TokenInvalidError:
        raise HTTPException(status_code=400, detail="Invalid token.")

    # Check 3: the token belongs to THIS order
    if claims["order_id"] != order["order_id"]:
        raise HTTPException(status_code=400, detail="Token does not match this order.")

    # Check 4: amount, currency and seller match OUR database, not the browser
    product = db.get_product(order["product_id"])
    if (
        not product
        or claims["amount_cents"] != order["amount_cents"]
        or claims["currency"] != order["currency"]
        or claims["seller_email"] != product["seller_email"]
    ):
        raise HTTPException(status_code=400, detail="Token does not match this order.")

        # Check 5: the outcome inside the token must allow capture
    outcome = claims["outcome"]
    if outcome == "High risk":
        raise HTTPException(status_code=403, detail="This payment was stopped by the safety check.")
    if outcome not in ("Low risk", "Suspicious", "Unknown"):
        raise HTTPException(status_code=400, detail="Invalid token.")

    # Check 6: Suspicious and Unknown need the buyer to confirm
    if outcome in ("Suspicious", "Unknown") and not payload.confirm:
        raise HTTPException(status_code=400, detail="Please confirm to continue.")

    # Check 7: Suspicious must wait. The server counts the time, not the browser.
    if outcome == "Suspicious":
        wait_seconds = int(os.getenv("WAIT_SECONDS", str(DEFAULT_WAIT_SECONDS)))
        if int(time.time()) - claims["iat"] < wait_seconds:
            raise HTTPException(status_code=403, detail="Please wait before confirming.")

    # Check 8: this token was really issued by us for this order
    assessment = db.get_assessment_by_jti(claims["jti"])
    if not assessment or assessment["order_id"] != order["order_id"]:
        raise HTTPException(status_code=400, detail="Invalid token.")

    # Check 9: use the token only once. This update is atomic.
    if not db.mark_jti_used(claims["jti"]):
        raise HTTPException(status_code=409, detail="This token was already used.")

    # All checks passed: only now does the server ask PayPal to take the money
    try:
        result = await paypal_client.capture_order(
            order["paypal_order_id"],
            request_id=f"capture_{order['order_id']}",
        )
    except Exception as e:
        logger.error("Capture failed for %s: %s", order["order_id"], e)
        db.log_audit("CAPTURE_FAILED", order["order_id"], "PayPal capture error")
        raise HTTPException(status_code=502, detail="The payment could not be completed. Please run the check again.")

    if result.get("status") != "COMPLETED":
        db.log_audit("CAPTURE_FAILED", order["order_id"], "PayPal status not completed")
        raise HTTPException(status_code=502, detail="The payment could not be completed. Please run the check again.")

    db.update_order_status(order["order_id"], "CAPTURED")
    db.log_audit("ORDER_CAPTURED", order["order_id"], f"Outcome: {outcome}")

    return {
        "status": "captured",
        "order_id": order["order_id"],
        "outcome": outcome,
    }
