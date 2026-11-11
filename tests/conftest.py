import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Use a throwaway database so tests never touch shieldpay.db.
_TMP = tempfile.mkdtemp(prefix="shieldpay_tests_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test.db")
os.environ["ADMIN_PASSWORD"] = "test-admin-password"
os.environ["PAYPAL_MODE"] = "mock"
os.environ["TOKEN_SECRET"] = "t" * 40
os.environ["PAYPAL_CLIENT_ID"] = "mock-client-id"
os.environ["PAYPAL_SECRET"] = "mock-secret"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def fresh_state():
    import database
    import security

    path = os.environ["DB_PATH"]
    if os.path.exists(path):
        os.remove(path)
    database.init_db()
    database.seed_demo_data()
    security.reset_limits()
    yield


@pytest.fixture
def client():
    from main import app

    with TestClient(app) as c:
        yield c