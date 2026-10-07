"""
Khmer TopUp Reseller API client
https://khmer-topup.com/api-docs
Base: https://khmer-topup.com/api/v1
"""
import os
import requests

API_KEY = os.getenv("KHMER_TOPUP_API_KEY", "")
BASE = "https://khmer-topup.com/api/v1"

_session = requests.Session()
_session.headers.update({
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json",
})


def is_ready() -> bool:
    return bool(API_KEY.strip())


def me() -> dict:
    if not is_ready():
        return {"error": "KHMER_TOPUP_API_KEY missing"}
    try:
        r = _session.get(f"{BASE}/me", timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def games() -> dict:
    if not is_ready():
        return {"games": [], "error": "API key missing"}
    try:
        r = _session.get(f"{BASE}/games", timeout=20)
        return r.json()
    except Exception as e:
        return {"games": [], "error": str(e)}


def check(slug: str, player_id: str, server_id: str = None) -> dict:
    if not is_ready():
        # demo fallback
        if len(player_id) >= 5:
            return {"result": "valid", "nickname": "DemoPlayer"}
        return {"result": "invalid"}
    try:
        params = {"slug": slug, "player_id": player_id}
        if server_id:
            params["server_id"] = server_id
        r = _session.get(f"{BASE}/check", params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"result": "unknown", "error": str(e)}


def place_order(package_id: int, player_id: str, server_id: str = None, reference: str = None) -> dict:
    if not is_ready():
        return {"error": "KHMER_TOPUP_API_KEY missing", "status": "failed"}
    body = {
        "package_id": package_id,
        "player_id": str(player_id),
    }
    if server_id:
        body["server_id"] = str(server_id)
    if reference:
        body["reference"] = reference
    try:
        r = _session.post(f"{BASE}/orders", json=body, timeout=30)
        data = r.json()
        data["_http"] = r.status_code
        return data
    except Exception as e:
        return {"error": str(e), "status": "failed"}


def order_status(order_code: str) -> dict:
    if not is_ready():
        return {"error": "API key missing"}
    try:
        r = _session.get(f"{BASE}/orders/{order_code}", timeout=15)
        return r.json()
    except Exception as e:
        return {"error": str(e)}
