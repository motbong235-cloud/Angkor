#!/usr/bin/env python3
"""
AngkorTopUp — Game Top-up Website
Payment: KHPay KHQR
Fulfillment: Khmer TopUp API (optional) or manual
Deploy-ready for Render
"""
import json
import os
import secrets
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, render_template, request, session

import khpay
import khmer_topup

BASE = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", str(BASE / "data")))
DB_PATH = DATA_DIR / "db.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_seed = BASE / "data" / "db.json"
if not DB_PATH.exists() and _seed.exists():
    DB_PATH.write_text(_seed.read_text(encoding="utf-8"), encoding="utf-8")

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(24))


def utc_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def db_read():
    if not DB_PATH.exists():
        return {
            "settings": {},
            "games": [],
            "orders": [],
            "next_order": 1001,
            "visitors": {},
        }
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def db_write(data):
    tmp = DB_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(DB_PATH)



def get_client_ip():
    """Get real client IP (supports Render / Cloudflare / proxy)."""
    # X-Forwarded-For: client, proxy1, proxy2
    xff = request.headers.get("X-Forwarded-For") or ""
    if xff:
        return xff.split(",")[0].strip()
    real = request.headers.get("X-Real-IP") or ""
    if real:
        return real.strip()
    return (request.remote_addr or "0.0.0.0").strip()


def track_visitor(ip=None):
    """Record unique visitor: 1 IP = 1 user. Returns (unique_count, is_new)."""
    if ip is None:
        ip = get_client_ip()
    if not ip or ip in ("0.0.0.0", "127.0.0.1", "::1"):
        # still count localhost in dev, but skip empty
        if not ip:
            return 0, False
    d = db_read()
    visitors = d.get("visitors") or {}
    now = utc_now()
    is_new = ip not in visitors
    if is_new:
        visitors[ip] = {
            "first_seen": now,
            "last_seen": now,
            "hits": 1,
            "ua": (request.headers.get("User-Agent") or "")[:200],
        }
    else:
        visitors[ip]["last_seen"] = now
        visitors[ip]["hits"] = int(visitors[ip].get("hits") or 0) + 1
        if not visitors[ip].get("ua"):
            visitors[ip]["ua"] = (request.headers.get("User-Agent") or "")[:200]
    d["visitors"] = visitors
    db_write(d)
    return len(visitors), is_new


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return jsonify({"ok": False, "error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    return wrapper


# ---------- Pages ----------
@app.route("/")
def home():
    try:
        track_visitor()
    except Exception:
        pass
    return render_template("index.html")


@app.route("/angkor-tp-0606")
def admin_page():
    return render_template("admin.html")

# old path redirects away (hide admin)
@app.route("/admin")
def admin_redirect():
    return ("Not Found", 404)


@app.route("/track")
def track_page():
    try:
        track_visitor()
    except Exception:
        pass
    return render_template("track.html")


# ---------- Public API ----------
@app.route("/api/catalog")
def catalog():
    d = db_read()
    s = d.get("settings") or {}
    games = [g for g in d.get("games", []) if g.get("active", True)]

    # If Khmer TopUp API ready, optionally merge live packages
    # (local games take priority for custom pricing markup)
    return jsonify({
        "ok": True,
        "settings": {
            "SITE_NAME": s.get("SITE_NAME", "AngkorTopUp"),
            "SITE_TAGLINE": s.get("SITE_TAGLINE", "Top-up ហ្គេមលឿន សុវត្ថិភាព"),
            "TELEGRAM": s.get("TELEGRAM", ""),
            "CONTACT_NOTE": s.get("CONTACT_NOTE", ""),
            "LOGO_URL": s.get("LOGO_URL") or "/static/img/logo.svg",
            "BANNER_URL": s.get("BANNER_URL") or "/static/img/banner.svg",
            "FAVICON_URL": s.get("FAVICON_URL") or "/static/img/favicon.svg",
            "AUTO_FULFILL": bool(s.get("AUTO_FULFILL", True)),
        },
        "games": games,
        "khpay_ready": khpay.is_ready(),
        "kt_ready": khmer_topup.is_ready(),
    })


@app.route("/api/verify", methods=["POST"])
def verify_player():
    body = request.get_json(force=True, silent=True) or {}
    slug = (body.get("slug") or "").strip()
    player_id = (body.get("player_id") or "").strip()
    server_id = (body.get("server_id") or "").strip() or None
    if not slug or not player_id:
        return jsonify({"ok": False, "error": "slug + player_id required"}), 400

    result = khmer_topup.check(slug, player_id, server_id)
    # Also allow local-only games without API
    if result.get("result") in ("valid", "invalid", "unknown", "incomplete"):
        return jsonify({"ok": True, **result})
    # Demo fallback
    if len(player_id) >= 5:
        return jsonify({"ok": True, "result": "valid", "nickname": "Player"})
    return jsonify({"ok": True, "result": "invalid"})


@app.route("/api/order", methods=["POST"])
def create_order():
    body = request.get_json(force=True, silent=True) or {}
    game_slug = (body.get("game_slug") or body.get("slug") or "").strip()
    package_id = body.get("package_id")
    player_id = (body.get("player_id") or "").strip()
    server_id = (body.get("server_id") or "").strip() or None
    buyer = (body.get("telegram") or body.get("contact") or "").strip() or (
        "guest_" + secrets.token_hex(3)
    )

    if not game_slug or not package_id or not player_id:
        return jsonify({"ok": False, "error": "game_slug, package_id, player_id required"}), 400

    d = db_read()
    game = next((g for g in d.get("games", []) if g.get("slug") == game_slug and g.get("active", True)), None)
    if not game:
        return jsonify({"ok": False, "error": "Game មិនមាន"}), 404

    pkg = next((p for p in game.get("packages", []) if str(p.get("id")) == str(package_id)), None)
    if not pkg:
        return jsonify({"ok": False, "error": "Package មិនមាន"}), 404

    price = float(pkg.get("price") or 0)
    if price <= 0:
        return jsonify({"ok": False, "error": "តម្លៃមិនត្រឹមត្រូវ"}), 400

    if not khpay.is_ready():
        return jsonify({
            "ok": False,
            "error": "KHPAY_API_KEY មិនទាន់កំណត់ — Admin ដាក់ ENV លើ Render",
        }), 502

    order_id = f"AT{d.get('next_order', 1001)}"
    d["next_order"] = int(d.get("next_order", 1001)) + 1

    order = {
        "id": order_id,
        "game_slug": game_slug,
        "game_name": game.get("name"),
        "package_id": pkg.get("id"),
        "package_name": pkg.get("name"),
        "kt_package_id": pkg.get("kt_package_id"),  # for Khmer TopUp API
        "price": price,
        "player_id": player_id,
        "server_id": server_id,
        "buyer": buyer,
        "status": "pending_payment",
        "khpay_txn": None,
        "kt_order_code": None,
        "nickname": None,
        "created_at": utc_now(),
        "paid_at": None,
        "delivered_at": None,
    }

    # Create KHPay QR
    resp = khpay.create_qr(
        amount=price,
        note=f"{game.get('name')} {pkg.get('name')} · {order_id}",
        metadata={"order_id": order_id, "game": game_slug, "player_id": player_id},
    )
    if not resp.get("success"):
        return jsonify({
            "ok": False,
            "error": resp.get("error") or "បង្កើត QR បរាជ័យ",
        }), 502

    order["khpay_txn"] = resp.get("transaction_id")
    d.setdefault("orders", []).insert(0, order)
    db_write(d)

    return jsonify({
        "ok": True,
        "order": order,
        "payment": {
            "PAYMENT_QR": resp.get("qr_image"),
            "PAYMENT_URL": resp.get("payment_url"),
            "ABAPAY_DEEPLINK": resp.get("abapay_deeplink"),
            "EXPIRES_IN": resp.get("expires_in", 180),
            "SHOP_NAME": (d.get("settings") or {}).get("SITE_NAME", "AngkorTopUp"),
            "TRANSACTION_ID": resp.get("transaction_id"),
        },
        "message": "ស្កេន KHQR ដើម្បីបង់ប្រាក់",
    })


def _try_fulfill(d, order):
    """After paid — try auto deliver via Khmer TopUp API, else mark waiting."""
    s = d.get("settings") or {}
    auto = bool(s.get("AUTO_FULFILL", True))
    order["paid_at"] = utc_now()
    order["status"] = "paid"

    kt_pkg = order.get("kt_package_id")
    if auto and khmer_topup.is_ready() and kt_pkg:
        ref = f"angkor-{order['id']}-{secrets.token_hex(3)}"
        result = khmer_topup.place_order(
            package_id=int(kt_pkg),
            player_id=order["player_id"],
            server_id=order.get("server_id"),
            reference=ref,
        )
        if result.get("order_code"):
            order["kt_order_code"] = result["order_code"]
            order["status"] = "processing"
            order["kt_status"] = result.get("status", "processing")
            # If already completed
            if result.get("status") == "completed":
                order["status"] = "completed"
                order["delivered_at"] = utc_now()
        else:
            order["status"] = "waiting_fulfill"
            order["kt_error"] = result.get("error") or str(result)[:200]
    else:
        order["status"] = "waiting_fulfill"

    return order


@app.route("/api/order/check-payment", methods=["POST"])
def check_payment():
    body = request.get_json(force=True, silent=True) or {}
    oid = (body.get("order_id") or body.get("id") or "").strip().upper()
    if not oid:
        return jsonify({"ok": False, "error": "Missing order_id"}), 400

    d = db_read()
    order = next((o for o in d.get("orders", []) if str(o.get("id", "")).upper() == oid), None)
    if not order:
        return jsonify({"ok": False, "error": "Order not found"}), 404

    if order.get("status") in ("paid", "processing", "completed", "waiting_fulfill", "delivered"):
        return jsonify({
            "ok": True,
            "order": order,
            "payment_status": "completed",
            "message": "Paid",
        })

    txn = order.get("khpay_txn")
    if not txn:
        return jsonify({"ok": True, "order": order, "payment_status": "pending"})

    resp = khpay.check_payment(txn)
    if resp.get("paid"):
        _try_fulfill(d, order)
        db_write(d)
        return jsonify({
            "ok": True,
            "order": order,
            "payment_status": "completed",
            "message": "បង់រួច!",
        })

    status = str(resp.get("status") or resp.get("action") or "pending").lower()
    return jsonify({
        "ok": True,
        "order": order,
        "payment_status": status,
        "message": "រង់ចាំបង់ប្រាក់",
    })


@app.route("/api/order/confirm-paid", methods=["POST"])
def confirm_paid():
    body = request.get_json(force=True, silent=True) or {}
    oid = (body.get("order_id") or body.get("id") or "").strip().upper()
    if not oid:
        return jsonify({"ok": False, "error": "Missing order_id"}), 400

    d = db_read()
    order = next((o for o in d.get("orders", []) if str(o.get("id", "")).upper() == oid), None)
    if not order:
        return jsonify({"ok": False, "error": "រកមិនឃើញ order"}), 404

    if order.get("status") not in ("pending_payment", "pending"):
        return jsonify({"ok": True, "order": order, "message": "Order រួចរាល់"})

    txn = order.get("khpay_txn")
    if not txn:
        return jsonify({"ok": False, "error": "គ្មាន transaction"}), 400

    resp = khpay.check_payment(txn)
    if not resp.get("paid"):
        return jsonify({
            "ok": False,
            "error": "KHPay មិនទាន់ទទួលប្រាក់",
            "payment_status": str(resp.get("status") or "pending"),
        }), 402

    _try_fulfill(d, order)
    db_write(d)
    return jsonify({"ok": True, "order": order, "message": "បង់រួច!"})


@app.route("/api/track")
def track_order():
    oid = (request.args.get("id") or "").strip().upper()
    if not oid:
        return jsonify({"ok": False, "error": "Missing order id"}), 400
    d = db_read()
    order = next((o for o in d.get("orders", []) if str(o.get("id", "")).upper() == oid), None)
    if not order:
        return jsonify({"ok": False, "error": "រកមិនឃើញ order"}), 404

    # Optionally refresh KT status
    if order.get("kt_order_code") and order.get("status") == "processing":
        st = khmer_topup.order_status(order["kt_order_code"])
        if st.get("status") == "completed":
            order["status"] = "completed"
            order["delivered_at"] = utc_now()
            db_write(d)
        elif st.get("status") == "refunded":
            order["status"] = "refunded"
            db_write(d)

    public = {
        "id": order["id"],
        "game_name": order.get("game_name"),
        "package_name": order.get("package_name"),
        "price": order.get("price"),
        "player_id": order.get("player_id"),
        "server_id": order.get("server_id"),
        "status": order.get("status"),
        "created_at": order.get("created_at"),
        "paid_at": order.get("paid_at"),
        "delivered_at": order.get("delivered_at"),
        "kt_order_code": order.get("kt_order_code"),
    }
    return jsonify({"ok": True, "order": public})


# ---------- Admin ----------
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    body = request.get_json(force=True, silent=True) or {}
    pw = body.get("password") or ""
    d = db_read()
    expected = d.get("settings", {}).get("ADMIN_PASSWORD", "admin123")
    if pw == expected or pw == os.environ.get("ADMIN_PASSWORD", ""):
        session["admin"] = True
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ពាក្យសម្ងាត់មិនត្រឹមត្រូវ"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    return jsonify({"ok": True})


@app.route("/api/admin/me")
def admin_me():
    return jsonify({"ok": True, "admin": bool(session.get("admin"))})


@app.route("/api/admin/data")
@admin_required
def admin_data():
    d = db_read()
    visitors = d.get("visitors") or {}
    # sort by last_seen desc
    visitor_list = []
    for ip, info in visitors.items():
        visitor_list.append({
            "ip": ip,
            "first_seen": info.get("first_seen", ""),
            "last_seen": info.get("last_seen", ""),
            "hits": int(info.get("hits") or 0),
            "ua": info.get("ua") or "",
        })
    visitor_list.sort(key=lambda x: x.get("last_seen") or "", reverse=True)
    total_hits = sum(v["hits"] for v in visitor_list)
    return jsonify({
        "ok": True,
        "settings": d.get("settings", {}),
        "games": d.get("games", []),
        "orders": d.get("orders", [])[:150],
        "khpay_ready": khpay.is_ready(),
        "kt_ready": khmer_topup.is_ready(),
        "storage_persistent": bool(os.environ.get("DATA_DIR")),
        "visitors": {
            "unique": len(visitor_list),
            "total_hits": total_hits,
            "list": visitor_list[:200],
        },
    })



@app.route("/api/admin/visitors/clear", methods=["POST"])
@admin_required
def admin_visitors_clear():
    d = db_read()
    d["visitors"] = {}
    db_write(d)
    return jsonify({"ok": True})


@app.route("/api/admin/game", methods=["POST", "PUT", "DELETE"])
@admin_required
def admin_game():
    d = db_read()
    body = request.get_json(force=True, silent=True) or {}

    if request.method == "DELETE":
        slug = body.get("slug")
        d["games"] = [g for g in d.get("games", []) if g.get("slug") != slug]
        db_write(d)
        return jsonify({"ok": True})

    if request.method == "POST":
        slug = (body.get("slug") or "").strip().lower().replace(" ", "-")
        if not slug:
            return jsonify({"ok": False, "error": "slug required"}), 400
        if any(g.get("slug") == slug for g in d.get("games", [])):
            return jsonify({"ok": False, "error": "slug already exists"}), 400
        game = {
            "slug": slug,
            "name": (body.get("name") or slug).strip(),
            "id_label": body.get("id_label") or "User ID",
            "server_label": body.get("server_label") or None,
            "emoji": body.get("emoji") or "🎮",
            "color": body.get("color") or "#3B82F6",
            "popular": bool(body.get("popular", False)),
            "active": True,
            "packages": body.get("packages") or [],
        }
        d.setdefault("games", []).append(game)
        db_write(d)
        return jsonify({"ok": True, "game": game})

    # PUT
    slug = body.get("slug")
    for g in d.get("games", []):
        if g.get("slug") == slug:
            for k in ("name", "id_label", "server_label", "emoji", "color", "packages"):
                if k in body:
                    g[k] = body[k]
            if "popular" in body:
                g["popular"] = bool(body["popular"])
            if "active" in body:
                g["active"] = bool(body["active"])
            db_write(d)
            return jsonify({"ok": True, "game": g})
    return jsonify({"ok": False, "error": "Not found"}), 404


@app.route("/api/admin/order", methods=["PATCH"])
@admin_required
def admin_order_patch():
    body = request.get_json(force=True, silent=True) or {}
    oid = body.get("id")
    d = db_read()
    for o in d.get("orders", []):
        if o["id"] == oid:
            if "status" in body:
                o["status"] = body["status"]
                if body["status"] in ("completed", "delivered"):
                    o["delivered_at"] = utc_now()
            if "note" in body:
                o["admin_note"] = body["note"]
            db_write(d)
            return jsonify({"ok": True, "order": o})
    return jsonify({"ok": False, "error": "Not found"}), 404


@app.route("/api/admin/settings", methods=["PUT"])
@admin_required
def admin_settings():
    body = request.get_json(force=True, silent=True) or {}
    d = db_read()
    s = d.setdefault("settings", {})
    for k in (
        "SITE_NAME", "SITE_TAGLINE", "TELEGRAM", "CONTACT_NOTE",
        "LOGO_URL", "BANNER_URL", "FAVICON_URL",
        "ADMIN_PASSWORD", "AUTO_FULFILL",
    ):
        if k in body and body[k] is not None:
            if k == "AUTO_FULFILL":
                s[k] = bool(body[k]) if not isinstance(body[k], str) else body[k] in ("1", "true", "True", True)
            else:
                s[k] = body[k]
    db_write(d)
    return jsonify({"ok": True, "settings": s})


@app.route("/api/admin/sync-games", methods=["POST"])
@admin_required
def admin_sync_games():
    """Pull games from Khmer TopUp API and merge into local catalog."""
    if not khmer_topup.is_ready():
        return jsonify({"ok": False, "error": "KHMER_TOPUP_API_KEY not set"}), 400
    data = khmer_topup.games()
    remote = data.get("games") or []
    if not remote:
        return jsonify({"ok": False, "error": data.get("error") or "No games returned"}), 400

    d = db_read()
    local = {g["slug"]: g for g in d.get("games", [])}
    added = 0
    updated = 0

    for rg in remote:
        slug = rg.get("slug") or ""
        if not slug:
            continue
        packages = []
        for i, p in enumerate(rg.get("packages") or []):
            packages.append({
                "id": p.get("package_id") or (1000 + i),
                "name": p.get("name") or f"Pack {i+1}",
                "price": float(p.get("price") or 0),
                "tag": p.get("tag"),
                "kt_package_id": p.get("package_id"),
            })
        if slug in local:
            # update packages prices from API
            local[slug]["packages"] = packages
            local[slug]["id_label"] = rg.get("id_label") or local[slug].get("id_label")
            local[slug]["server_label"] = rg.get("server_label")
            updated += 1
        else:
            local[slug] = {
                "slug": slug,
                "name": rg.get("name") or slug,
                "id_label": rg.get("id_label") or "User ID",
                "server_label": rg.get("server_label"),
                "emoji": "🎮",
                "color": "#3B82F6",
                "popular": False,
                "active": True,
                "packages": packages,
            }
            added += 1

    d["games"] = list(local.values())
    db_write(d)
    return jsonify({"ok": True, "added": added, "updated": updated, "total": len(d["games"])})


@app.route("/health")
def health():
    return jsonify({
        "ok": True,
        "service": "AngkorTopUp",
        "khpay": khpay.is_ready(),
        "khmer_topup": khmer_topup.is_ready(),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG") == "1")
