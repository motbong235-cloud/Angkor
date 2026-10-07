"""
KHPAY Module — KHQR / ABA PayWay (khpay.site)
"""
import os
import requests

KHPAY_API_KEY = os.getenv("KHPAY_API_KEY", "")
BASE_URL = "https://khpay.site/api/v1"

_session = requests.Session()
_session.headers.update({
    "Authorization": f"Bearer {KHPAY_API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
})


def is_ready() -> bool:
    return bool(KHPAY_API_KEY.strip())


def create_qr(
    amount: float,
    note: str = "Payment",
    callback_url: str = None,
    success_url: str = None,
    cancel_url: str = None,
    metadata: dict = None,
    merchant_id: str = None,
) -> dict:
    if not is_ready():
        return {"success": False, "error": "KHPAY_API_KEY មិនទាន់កំណត់"}

    payload = {
        "amount": f"{float(amount):.2f}",
        "currency": "USD",
        "note": note,
    }
    if callback_url:
        payload["callback_url"] = callback_url
    if success_url:
        payload["success_url"] = success_url
    if cancel_url:
        payload["cancel_url"] = cancel_url
    if metadata:
        payload["metadata"] = metadata
    if merchant_id:
        payload["merchant_id"] = merchant_id

    try:
        r = _session.post(f"{BASE_URL}/qr/generate", json=payload, timeout=20)
        data = r.json()
        if data.get("success") and data.get("data"):
            d = data["data"]
            return {
                "success": True,
                "transaction_id": d.get("transaction_id"),
                "qr_string": d.get("qr_string"),
                "qr_image": d.get("qr_image"),
                "payment_url": d.get("payment_url"),
                "abapay_deeplink": d.get("abapay_deeplink"),
                "expires_in": d.get("expires_in", 180),
                "download_qr": d.get("download_qr"),
                "raw": data,
            }
        return {
            "success": False,
            "error": data.get("error") or data.get("message") or "បង្កើត QR មិនបាន",
            "error_code": data.get("error_code"),
            "raw": data,
        }
    except requests.Timeout:
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def check_payment(transaction_id: str) -> dict:
    if not is_ready():
        return {"paid": False, "error": "API Key មិនទាន់កំណត់"}
    try:
        r = _session.get(f"{BASE_URL}/qr/check/{transaction_id}", timeout=15)
        data = r.json()
        if data.get("success") and data.get("data"):
            d = data["data"]
            paid = (
                d.get("paid") is True
                or str(d.get("status", "")).lower() == "paid"
                or d.get("action") == "approved"
            )
            return {
                "paid": paid,
                "status": d.get("status"),
                "action": d.get("action"),
                "amount": d.get("amount"),
                "currency": d.get("currency"),
                "raw": data,
            }
        return {
            "paid": False,
            "error": data.get("error") or "មិនអាចពិនិត្យបាន",
            "raw": data,
        }
    except Exception as e:
        return {"paid": False, "error": str(e)}


def expire_payment(transaction_id: str) -> dict:
    if not is_ready():
        return {"success": False, "error": "API Key មិនទាន់កំណត់"}
    try:
        r = _session.post(f"{BASE_URL}/qr/expire/{transaction_id}", timeout=10)
        data = r.json()
        return {
            "success": data.get("success", False),
            "message": data.get("message"),
            "raw": data,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
