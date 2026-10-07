# ⚡ AngkorTopUp — Full (KHPay + Render)

Website **Top-up ហ្គេម**  
**Payment:** [KHPay](https://khpay.site) KHQR  
**Fulfill:** [Khmer TopUp](https://khmer-topup.com) API (optional)  
**Deploy:** Render.com

---

## 🔄 Flow

```
ជ្រើសហ្គេម → Package → Player ID → Verify
        ↓
POST /api/order → khpay.create_qr()
        ↓
បង្ហាញ KHQR · poll 4s
        ↓
paid → AUTO_FULFILL
  ├─ មាន KHMER_TOPUP_API_KEY → deliver Diamonds
  └─ គ្មាន → waiting_fulfill → Admin mark Done
```

---

## 🚀 Deploy Render (Full)

### 1. Push ទៅ GitHub
```bash
cd angkor-topup-render
git init && git add . && git commit -m "AngkorTopUp"
# push to your repo
```

### 2. Render → New Web Service
- **Runtime:** Python 3
- **Build:** `pip install -r requirements.txt`
- **Start:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`

### 3. Environment Variables

| Key | Required | តម្លៃ |
|-----|----------|--------|
| `KHPAY_API_KEY` | ✅ | ពី [khpay.site](https://khpay.site) |
| `KHMER_TOPUP_API_KEY` | optional | Reseller key ពី khmer-topup.com |
| `ADMIN_PASSWORD` | ✅ | ពាក្យសម្ងាត់ admin |
| `SECRET_KEY` | ✅ | random long string |
| `DATA_DIR` | ✅ | `/var/data` |

### 4. Disk (សំខាន់!)
- Name: `angkor-data`
- Mount: `/var/data`
- Size: 1 GB

### 5. ឬប្រើ Blueprint
Upload `render.yaml` → Render New Blueprint

---

## 🖥️ Local

```bash
pip install -r requirements.txt
export KHPAY_API_KEY=your_key
export ADMIN_PASSWORD=admin123
python app.py
```
- Shop: http://localhost:5000  
- Admin: http://localhost:5000/angkor-tp-0606  

---

## 🔑 យក Keys

**KHPay** (អតិថិជនបង់): https://khpay.site → API Key  
**Khmer TopUp** (auto deliver): https://khmer-topup.com → Reseller → API Key + Top-up Wallet

Admin → **Sync ពី Khmer TopUp** ដើម្បីទាញ games/packages ពិត

---

## 📁 Structure

```
app.py, khpay.py, khmer_topup.py
templates/index.html, track.html, admin.html
static/css, static/js
data/db.json
requirements.txt, Procfile, render.yaml
```
