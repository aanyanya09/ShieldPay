"""
paypal_client.py - PayPal Sandbox Orders API v2 Client for ShieldPay (§4, B1, B2).
Strict server-to-server calls; no secrets are ever exposed to the client (§7, B6).
Supports PayPal-Request-Id idempotency headers.
"""

import os
import logging
import httpx
from typing import Dict, Any, Optional

logger = logging.getLogger("shieldpay.paypal")


class PayPalClient:
    def __init__(
        self,
        client_id: Optional[str] = None,
        secret: Optional[str] = None,
        mode: Optional[str] = None
    ):
        self._client_id = client_id
        self._secret = secret
        self._mode = mode
        self._access_token: Optional[str] = None

    @property
    def client_id(self) -> str:
        return self._client_id or os.getenv("PAYPAL_CLIENT_ID", "")

    @property
    def secret(self) -> str:
        return self._secret or os.getenv("PAYPAL_SECRET", "")

    @property
    def mode(self) -> str:
        return (self._mode or os.getenv("PAYPAL_MODE", "sandbox")).lower()

    @property
    def base_url(self) -> str:
        if self.mode == "live":
            raise RuntimeError("Live mode is disabled: ShieldPay is Sandbox only.")
        return "https://api-m.sandbox.paypal.com"

    @property
    def is_configured(self) -> bool:
        """True if non-empty, non-mock credentials are provided."""
        if self.mode == "mock" or self.client_id.startswith("mock") or not self.client_id.strip():
            return False
        return bool(self.client_id.strip() and self.secret.strip())
    
    @property
    def is_mock(self) -> bool:
        """True only when PAYPAL_MODE=mock was set on purpose (tests, local demo)."""
        return self.mode == "mock"

    async def get_access_token(self) -> str:
        """Fetches OAuth2 bearer token from PayPal Sandbox."""
        if not self.is_configured:
            raise RuntimeError("PayPal credentials are not configured.")

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.secret),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json", "Accept-Language": "en_US"}
            )
            if resp.status_code != 200:
                logger.error("PayPal OAuth failed: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"PayPal OAuth failed with status {resp.status_code}")
            data = resp.json()
            token = data.get("access_token", "")
            if not token:
                raise RuntimeError("PayPal OAuth returned no access token")
            self._access_token = token
            return token

    async def create_order(
        self,
        order_id: str,
        amount_cents: int,
        currency: str,
        description: str,
        seller_email: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a PayPal order via Orders v2 API (§4, B1).
        Amount is formatted as two decimal places (e.g. 4999 -> '49.99').
        """
        amount_decimal = f"{amount_cents / 100.0:.2f}"

        # If PayPal credentials are not configured yet, return a simulated order for local dev
        if self.is_mock:
            logger.info("Using simulated PayPal sandbox order for %s", order_id)
            return {
                "id": f"SANDBOX_ORDER_{order_id}",
                "status": "CREATED",
                "simulated": True,
                "amount": {"currency_code": currency, "value": amount_decimal}
            }
        if not self.is_configured:
            raise RuntimeError("PayPal credentials are not configured.")

        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": f"create_{order_id}"
        }

        payload: Dict[str, Any] = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": order_id,
                    "description": description[:127],
                    "amount": {
                        "currency_code": currency,
                        "value": amount_decimal
                    }
                }
            ]
        }

        if return_url and cancel_url:
            payload["payment_source"] = {
                "paypal": {
                    "experience_context": {
                        "return_url": return_url,
                        "cancel_url": cancel_url,
                        "user_action": "PAY_NOW",
                        "shipping_preference": "NO_SHIPPING",
                    }
                }
            }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers=headers,
                json=payload
            )
            if resp.status_code not in (200, 201):
                logger.error("PayPal order creation failed: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"PayPal order creation failed: {resp.text}")
            return resp.json()

    async def capture_order(
        self,
        paypal_order_id: str,
        request_id: str
    ) -> Dict[str, Any]:
        """
        Capture a PayPal order (§4, B2).
        Sends PayPal-Request-Id header to guarantee idempotency.
        """
        if self.is_mock:
            logger.info("Simulating PayPal capture for %s with request_id %s", paypal_order_id, request_id)
            return {
                "id": paypal_order_id,
                "status": "COMPLETED",
                "simulated": True,
                "capture_id": f"SIM_CAP_{request_id}"
            }
        if not self.is_configured:
            raise RuntimeError("PayPal credentials are not configured.")

        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": request_id
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{self.base_url}/v2/checkout/orders/{paypal_order_id}/capture",
                headers=headers,
                json={}
            )
            if resp.status_code not in (200, 201):
                logger.error("PayPal capture failed: %s %s", resp.status_code, resp.text)
                raise RuntimeError(f"PayPal capture failed: {resp.text}")
            return resp.json()
    @staticmethod
    def approval_url(order: Dict[str, Any]) -> Optional[str]:
        for link in order.get("links", []):
            if link.get("rel") in ("payer-action", "approve"):
                return link.get("href")
        return None

    async def get_order(self, paypal_order_id: str) -> Dict[str, Any]:
        """Read an order's status from PayPal (APPROVED means the buyer approved)."""
        if self.is_mock:
            return {"id": paypal_order_id, "status": "APPROVED", "simulated": True}
        if not self.is_configured:
            raise RuntimeError("PayPal credentials are not configured.")
        token = await self.get_access_token()
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{self.base_url}/v2/checkout/orders/{paypal_order_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code != 200:
                raise RuntimeError(f"PayPal get order failed: {resp.status_code}")
            return resp.json()
