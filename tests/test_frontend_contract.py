def test_frontend_api_contract_order_assess_capture(client):
    products_response = client.get("/api/products")
    assert products_response.status_code == 200
    products = products_response.json()["products"]
    assert products
    product = next(item for item in products if item["product_id"] == "prod_headphones_101")

    order_response = client.post(
        "/api/orders",
        json={"product_id": product["product_id"], "quantity": 2},
    )
    assert order_response.status_code == 201
    order = order_response.json()
    assert order["order_id"]
    assert order["amount_cents"] == product["price_cents"] * 2
    assert order["currency"] == product["currency"]

    assessment_response = client.post(
        "/api/assess",
        json={"order_id": order["order_id"], "message": "", "answers": [False, False, False]},
    )
    assert assessment_response.status_code == 200
    assessment = assessment_response.json()
    assert "outcome" in assessment
    assert "token" in assessment

    capture_response = client.post(
        "/api/capture",
        json={"order_id": order["order_id"], "token": assessment["token"], "confirm": True},
    )
    assert capture_response.status_code == 200
    assert capture_response.json()["status"] == "captured"


def test_frontend_report_contract(client):
    response = client.post(
        "/api/reports",
        json={"seller_email": "reported-seller@example.com", "reason": "Suspicious refund request"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "received"
    assert response.json()["report_status"] == "Unverified"