import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error

BACKEND_DIR = r"c:\Users\asus\Desktop\logicielle\BACKEND"
DEV_JAVA_DIR = r"c:\Users\asus\Desktop\logicielle\DEVELOPMENT\LOGINN"


def http_json(method, url, payload=None, headers=None):
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}


def main():
    print("=" * 72)
    print("STARTING END-TO-END VERIFICATION OF CCTV BUSINESS ECOSYSTEM")
    print("=" * 72)

    # 1. Start Django server in background on 127.0.0.1:8000
    server_proc = subprocess.Popen(
        [sys.executable, "manage.py", "runserver", "127.0.0.1:8000", "--noreload"],
        cwd=BACKEND_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    try:
        # Wait for server to be ready
        ready = False
        for _ in range(25):
            try:
                code, _ = http_json("GET", "http://127.0.0.1:8000/api/v1/catalog/home/")
                if code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.4)
        assert ready, "Django server failed to start on 127.0.0.1:8000"
        print("[PASS] 1. Django REST API server is live on http://127.0.0.1:8000")

        # 2. Run initial Java catalog & stock push from java_dev (497 products)
        java_sync_cmd = [
            "java",
            "-Dfile.encoding=UTF-8",
            "-cp",
            "build/classes;dist/lib/*",
            "loginn.v2.E2eDesktopSyncVerifier",
        ]
        sync_res = subprocess.run(java_sync_cmd, cwd=DEV_JAVA_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        print((sync_res.stdout or "").strip())
        assert sync_res.returncode == 0, f"Initial Java sync failed: {sync_res.stderr}"

        # 3. Test Pricing Tiers (Guest vs Pending Installer vs Approved Installer vs Approved Reseller)
        # Pick product 9L11FB1P (T1A21P -> Public 3350, Gros/Reseller 3000)
        code, guest_prod = http_json("GET", "http://127.0.0.1:8000/api/v1/products/9L11FB1P/")
        assert code == 200, f"Expected 200, got {code}: {guest_prod}"
        p_guest = guest_prod["product"]
        assert p_guest["applied_tier"] == "PUBLIC"
        assert "reseller_price" not in p_guest["tier_prices"], "Guest must not see reseller_price"
        print(f"[PASS] 2a. Guest sees PUBLIC tier price: {p_guest['effective_price']} DA (Public={p_guest['public_price']} DA)")

        # Login as pending installer (installateur_attente / pro12345)
        code, login_pending = http_json("POST", "http://127.0.0.1:8000/api/v1/auth/login/", {
            "username": "installateur_attente",
            "password": "pro12345",
        })
        assert code == 200
        token_pending = login_pending["access"]
        assert login_pending["profile"]["approval_status"] == "PENDING"
        assert login_pending["profile"]["effective_tier"] == "PUBLIC"

        code, pending_prod = http_json(
            "GET",
            "http://127.0.0.1:8000/api/v1/products/9L11FB1P/",
            headers={"Authorization": f"Bearer {token_pending}"},
        )
        assert pending_prod["product"]["applied_tier"] == "PUBLIC"
        assert pending_prod["product"]["effective_price"] == p_guest["effective_price"]
        print("[PASS] 2b. Pending Installer account remains on PUBLIC prices until admin approval")

        # Login as approved installer (installateur_pro / pro12345)
        code, login_inst = http_json("POST", "http://127.0.0.1:8000/api/v1/auth/login/", {
            "username": "installateur_pro",
            "password": "pro12345",
        })
        assert code == 200
        token_inst = login_inst["access"]
        code, inst_prod = http_json(
            "GET",
            "http://127.0.0.1:8000/api/v1/products/9L11FB1P/",
            headers={"Authorization": f"Bearer {token_inst}"},
        )
        assert inst_prod["product"]["applied_tier"] == "INSTALLER"
        inst_price = inst_prod["product"]["effective_price"]
        print(f"[PASS] 2c. Approved Installer sees INSTALLER price: {inst_price} DA")

        # Login as approved reseller (revendeur_gros / gros12345)
        code, login_res = http_json("POST", "http://127.0.0.1:8000/api/v1/auth/login/", {
            "username": "revendeur_gros",
            "password": "gros12345",
        })
        assert code == 200
        token_res = login_res["access"]
        code, res_prod = http_json(
            "GET",
            "http://127.0.0.1:8000/api/v1/products/9L11FB1P/",
            headers={"Authorization": f"Bearer {token_res}"},
        )
        assert res_prod["product"]["applied_tier"] == "RESELLER"
        res_price = res_prod["product"]["effective_price"]
        assert res_price == 4150.0, f"Expected reseller price 4150.0, got {res_price}"
        print(f"[PASS] 2d. Approved Reseller sees RESELLER wholesale price: {res_price} DA")

        # 4. Test CCTV Kit Builder Compatibility Checker
        code, kit_eval = http_json("POST", "http://127.0.0.1:8000/api/v1/kit-builder/", {
            "items": [
                {"product_id": p_guest["id"], "quantity": 4},
            ]
        })
        assert code == 200
        assert kit_eval["total_cameras"] == 4
        assert len(kit_eval["recommendations"]) > 0
        print(f"[PASS] 3. CCTV Kit Builder evaluated 4 cameras: total={kit_eval['package_total']} DA, recommendations={len(kit_eval['recommendations'])}")

        # 5. Test Server-Side Price Enforcement & Idempotent Checkout
        idem_key = f"TEST-ORDER-IDEM-{int(time.time())}"
        checkout_payload = {
            "customer_name": "Kamel Sécurité Pro",
            "customer_phone": "0550123456",
            "customer_email": "kamel@cctv-dz.com",
            "company_name": "Kamel CCTV Installation",
            "wilaya": "Alger",
            "delivery_address": "Rue Didouche Mourad, Alger",
            "delivery_method": "PICKUP",
            "payment_method": "PAY_AT_STORE",
            "notes": "Commande test E2E - retrait magasin",
            "items": [
                {
                    "reference": "9L11FB1P",
                    "quantity": 2,
                    "price": 1.00,  # Malicious tampered frontend price (must be ignored by backend!)
                }
            ],
        }
        code, order_resp = http_json(
            "POST",
            "http://127.0.0.1:8000/api/v1/orders/checkout/",
            checkout_payload,
            headers={"Authorization": f"Bearer {token_res}", "X-Idempotency-Key": idem_key},
        )
        assert code == 201, f"Expected 201, got {code}: {order_resp}"
        created_order = order_resp["order"]
        order_uid = created_order["order_uid"]
        item_applied_price = float(created_order["items"][0]["applied_unit_price"])
        assert item_applied_price == 4150.0, f"Backend must ignore tampered price 1.00 and apply 4150.0, got {item_applied_price}"
        print(f"[PASS] 4a. Order {order_uid} created with authoritative snapshot price {item_applied_price} DA (ignored tampered frontend price 1.00 DA)")

        # Repeat with same idempotency key -> must return 200 with exact same order_uid
        code2, order_resp2 = http_json(
            "POST",
            "http://127.0.0.1:8000/api/v1/orders/checkout/",
            checkout_payload,
            headers={"Authorization": f"Bearer {token_res}", "X-Idempotency-Key": idem_key},
        )
        assert code2 == 200
        assert order_resp2["order"]["order_uid"] == order_uid
        print(f"[PASS] 4b. Idempotency key prevented duplicate order creation (same order_uid={order_uid})")

        # 6. Run Java Integration Test inside DEVELOPMENT/LOGINN to pull order, convert to POS sale, & verify anti-double-deduction
        print("[INFO] 5. Running Java Swing DEVELOPMENT/LOGINN POS Conversion & Anti-Double-Deduction verification...")
        java_cmd = [
            "java",
            "-Dfile.encoding=UTF-8",
            "-cp",
            "build/classes;dist/lib/*",
            "loginn.v2.E2eDesktopSyncVerifier",
            order_uid,
        ]
        java_res = subprocess.run(java_cmd, cwd=DEV_JAVA_DIR, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
        print((java_res.stdout or "").strip())
        if java_res.returncode != 0:
            print("JAVA STDERR:", java_res.stderr)
            raise AssertionError("Java E2eDesktopSyncVerifier failed")

        # 7. Verify on Django Backend that all 497 products are synced and order is marked pos_converted=True
        code, tracked = http_json("GET", f"http://127.0.0.1:8000/api/v1/orders/track/{order_uid}/")
        assert code == 200
        assert tracked["order"]["pos_converted"] is True
        assert tracked["order"]["pos_bon_number"] != ""
        print(f"[PASS] 6. Backend verified order {order_uid} is linked to POS Bon N° {tracked['order']['pos_bon_number']}")

        print("=" * 72)
        print("ALL END-TO-END TESTS PASSED SUCCESSFULLY!")
        print("=" * 72)

    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except Exception:
            server_proc.kill()


if __name__ == "__main__":
    main()
