/**
 * AngkorTopUp — Frontend
 * Demo: mock verify/order
 * Production: /api/* → Flask → KHPay + Khmer TopUp
 */
const USE_API = true; // true = call Flask backend
const API_BASE = "/api";

let currentGame = null;
let selectedPackage = null;
let verifiedNickname = null;
let currentStep = 1;
let _poll = null;

document.addEventListener("DOMContentLoaded", () => {
  loadCatalog();
  setupEventListeners();
});

async function loadCatalog() {
  if (USE_API) {
    try {
      const r = await fetch(API_BASE + "/catalog");
      const data = await r.json();
      if (data.ok && data.settings) {
        applyBranding(data.settings);
      }
      if (data.ok && data.games && data.games.length) {
        // map API games to GAMES shape if needed
        window.GAMES = data.games.map((g) => ({
          slug: g.slug,
          name: g.name,
          id_label: g.id_label || "User ID",
          server_label: g.server_label || null,
          popular: !!g.popular,
          color: g.color || "#6366f1",
          emoji: g.emoji || "🎮",
          packages: (g.packages || []).map((p) => ({
            package_id: p.id || p.package_id,
            name: p.name,
            price: Number(p.price),
            tag: p.tag || null,
          })),
        }));
      }
    } catch (e) {
      console.warn("catalog API failed, using mock", e);
    }
  }
  if (!window.GAMES || !window.GAMES.length) {
    // fallback already in data.js
  }
  renderGames(window.GAMES || GAMES);
  renderTicker();
}

function renderGames(games) {
  const grid = document.getElementById("gamesGrid");
  if (!grid) return;
  grid.innerHTML = games
    .map(
      (g) => `
    <div class="game-card ${g.popular ? "popular" : ""}" onclick="openTopup('${g.slug}')">
      <div class="game-img" style="background:${g.color}33">${g.emoji}</div>
      <div class="game-name">${g.name}</div>
    </div>`
    )
    .join("");
}

function renderTicker() {
  const ticker = document.getElementById("liveTicker");
  if (!ticker || !window.TICKER_MESSAGES) return;
  const items = [...TICKER_MESSAGES, ...TICKER_MESSAGES]
    .map(
      (m) =>
        `<span class="ticker-item"><strong>${m.user}</strong> bought ${m.game} ${m.pkg} <strong>${m.price}</strong></span>`
    )
    .join("");
  ticker.innerHTML = items;
}

function setupEventListeners() {
  const search = document.getElementById("gameSearch");
  if (search) {
    search.addEventListener("input", (e) => {
      const q = e.target.value.toLowerCase().trim();
      const list = window.GAMES || GAMES;
      renderGames(
        list.filter(
          (g) => g.name.toLowerCase().includes(q) || g.slug.includes(q)
        )
      );
    });
  }
  document.getElementById("menuToggle")?.addEventListener("click", () => {
    document.getElementById("mobileMenu")?.classList.toggle("open");
  });
  document.querySelectorAll(".faq-q").forEach((btn) => {
    btn.addEventListener("click", () =>
      btn.parentElement.classList.toggle("open")
    );
  });
  document.querySelectorAll("[data-close]").forEach((el) => {
    el.addEventListener("click", closeModal);
  });
  document.getElementById("btnVerify")?.addEventListener("click", verifyAccount);
  document
    .getElementById("btnPlaceOrder")
    ?.addEventListener("click", placeOrder);
  document.getElementById("btnBack")?.addEventListener("click", goBack);
}

function openTopup(slug) {
  const list = window.GAMES || GAMES;
  currentGame = list.find((g) => g.slug === slug);
  if (!currentGame) return;
  selectedPackage = null;
  verifiedNickname = null;
  currentStep = 1;
  if (_poll) clearInterval(_poll);

  document.getElementById("modalGameName").textContent = currentGame.name;
  document.getElementById("modalGameSlug").textContent = currentGame.slug;
  const em = document.getElementById("modalGameEmoji");
  if (em) {
    em.textContent = currentGame.emoji;
    em.style.background = (currentGame.color || "#6366f1") + "33";
  }
  document.getElementById("labelPlayerId").textContent =
    currentGame.id_label || "Player ID";
  const sg = document.getElementById("serverGroup");
  if (currentGame.server_label) {
    sg.style.display = "block";
    document.getElementById("labelServerId").textContent =
      currentGame.server_label;
  } else {
    sg.style.display = "none";
  }

  document.getElementById("packagesGrid").innerHTML = currentGame.packages
    .map(
      (p) => `
    <div class="pkg-card" data-id="${p.package_id}" onclick="selectPackage(${p.package_id})">
      <div class="pkg-name">${p.name}</div>
      <div class="pkg-price">$${p.price.toFixed(2)}</div>
      ${p.tag ? `<span class="pkg-tag">${p.tag}</span>` : ""}
    </div>`
    )
    .join("");

  document.getElementById("playerId").value = "";
  document.getElementById("serverId").value = "";
  document.getElementById("verifyResult").className = "verify-result";
  document.getElementById("verifyResult").textContent = "";
  document.getElementById("selectedPkgInfo").textContent = "";

  // restore confirm step (may have been replaced by QR)
  const sc = document.getElementById("stepConfirm");
  if (sc) {
    sc.innerHTML = `
      <h4>បញ្ជាក់ Order</h4>
      <div class="order-summary" id="orderSummary"></div>
      <div class="payment-note">
        <p>💡 បន្ទាប់ពីបញ្ជាទិញ នឹងបង្ហាញ <strong>KHQR</strong> ដើម្បីស្កេនបង់ប្រាក់ (KHPay)។</p>
      </div>
      <button class="btn btn-primary btn-block btn-lg" id="btnPlaceOrder">បញ្ជាទិញ & បង់ប្រាក់</button>
    `;
    document.getElementById("btnPlaceOrder")?.addEventListener("click", placeOrder);
  }

  showStep(1);
  document.getElementById("topupModal").classList.add("open");
  document.body.style.overflow = "hidden";
}

function selectPackage(packageId) {
  selectedPackage = currentGame.packages.find(
    (p) => p.package_id === packageId
  );
  if (!selectedPackage) return;
  document
    .querySelectorAll(".pkg-card")
    .forEach((c) => c.classList.remove("selected"));
  document
    .querySelector(`.pkg-card[data-id="${packageId}"]`)
    ?.classList.add("selected");
  document.getElementById("selectedPkgInfo").textContent =
    `${selectedPackage.name} — $${selectedPackage.price.toFixed(2)}`;
  setTimeout(() => {
    currentStep = 2;
    showStep(2);
  }, 180);
}

function showStep(step) {
  currentStep = step;
  document
    .querySelectorAll(".modal-step")
    .forEach((s) => s.classList.remove("active"));
  const map = {
    1: "stepPackages",
    2: "stepPlayer",
    3: "stepConfirm",
    4: "stepSuccess",
  };
  // also support stepPay if we inject it
  const el = document.getElementById(map[step] || "stepConfirm");
  if (el) el.classList.add("active");
  // pay step uses stepConfirm area when showing QR
  if (step === "pay") {
    document.getElementById("stepConfirm")?.classList.add("active");
  }
  const btnBack = document.getElementById("btnBack");
  if (btnBack)
    btnBack.style.display = step > 1 && step < 4 ? "inline-flex" : "none";
  if (step === 3) renderOrderSummary();
}

function goBack() {
  if (currentStep === 2) showStep(1);
  else if (currentStep === 3) showStep(2);
}

async function verifyAccount() {
  const playerId = document.getElementById("playerId").value.trim();
  const serverId = document.getElementById("serverId").value.trim();
  const resultEl = document.getElementById("verifyResult");
  const btn = document.getElementById("btnVerify");
  if (!playerId) {
    resultEl.className = "verify-result invalid";
    resultEl.textContent = "សូមបញ្ចូល Player ID";
    return;
  }
  if (currentGame.server_label && !serverId) {
    resultEl.className = "verify-result invalid";
    resultEl.textContent = "សូមបញ្ចូល " + currentGame.server_label;
    return;
  }
  btn.disabled = true;
  btn.textContent = "កំពុងផ្ទៀងផ្ទាត់...";

  try {
    if (USE_API) {
      const r = await fetch(API_BASE + "/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: currentGame.slug,
          player_id: playerId,
          server_id: serverId || undefined,
        }),
      });
      const data = await r.json();
      if (data.result === "valid") {
        verifiedNickname = data.nickname || "Player";
        resultEl.className = "verify-result valid";
        resultEl.innerHTML = `✓ Account ត្រឹមត្រូវ — <strong>${verifiedNickname}</strong>`;
        setTimeout(() => showStep(3), 500);
      } else if (data.result === "invalid") {
        resultEl.className = "verify-result invalid";
        resultEl.textContent = "✗ Account មិនត្រឹមត្រូវ";
      } else {
        verifiedNickname = null;
        resultEl.className = "verify-result valid";
        resultEl.textContent = "✓ បន្តបាន";
        setTimeout(() => showStep(3), 500);
      }
    } else {
      await new Promise((r) => setTimeout(r, 700));
      if (playerId.length >= 5) {
        verifiedNickname = "DemoPlayer";
        resultEl.className = "verify-result valid";
        resultEl.innerHTML = `✓ <strong>${verifiedNickname}</strong>`;
        setTimeout(() => showStep(3), 500);
      } else {
        resultEl.className = "verify-result invalid";
        resultEl.textContent = "✗ Account មិនត្រឹមត្រូវ";
      }
    }
  } catch (e) {
    resultEl.className = "verify-result invalid";
    resultEl.textContent = "Error: " + e.message;
  }
  btn.disabled = false;
  btn.textContent = "ផ្ទៀងផ្ទាត់ Account";
}

function renderOrderSummary() {
  const playerId = document.getElementById("playerId").value.trim();
  const serverId = document.getElementById("serverId").value.trim();
  document.getElementById("orderSummary").innerHTML = `
    <div class="row"><span>ហ្គេម</span><span>${currentGame.name}</span></div>
    <div class="row"><span>Package</span><span>${selectedPackage.name}</span></div>
    <div class="row"><span>${currentGame.id_label}</span><span>${playerId}</span></div>
    ${serverId ? `<div class="row"><span>${currentGame.server_label}</span><span>${serverId}</span></div>` : ""}
    ${verifiedNickname ? `<div class="row"><span>Nickname</span><span>${verifiedNickname}</span></div>` : ""}
    <div class="row total"><span>សរុប</span><span>$${selectedPackage.price.toFixed(2)}</span></div>
  `;
  // restore buy button if was replaced by QR
  const confirm = document.getElementById("stepConfirm");
  if (confirm && !document.getElementById("btnPlaceOrder")) {
    // rebuild confirm step structure if needed
  }
}

async function placeOrder() {
  const btn = document.getElementById("btnPlaceOrder");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "កំពុងបង្កើត QR...";
  }
  const playerId = document.getElementById("playerId").value.trim();
  const serverId = document.getElementById("serverId").value.trim();

  try {
    const r = await fetch(API_BASE + "/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        game_slug: currentGame.slug,
        package_id: selectedPackage.package_id,
        player_id: playerId,
        server_id: serverId || undefined,
      }),
    });
    const data = await r.json();
    if (!data.ok) {
      alert(data.error || "បរាជ័យ");
      if (btn) {
        btn.disabled = false;
        btn.textContent = "បញ្ជាទិញឥឡូវនេះ";
      }
      return;
    }
    const o = data.order;
    const pay = data.payment || {};
    // Show KHQR in confirm step
    const step = document.getElementById("stepConfirm");
    step.innerHTML = `
      <h4>ស្កេន KHQR ដើម្បីបង់ប្រាក់</h4>
      <div class="order-summary" style="text-align:center">
        <div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:6px">${pay.SHOP_NAME || "AngkorTopUp"} · KHPay</div>
        <div style="font-size:1.6rem;font-weight:800;color:var(--accent);margin:8px 0">$${Number(o.price).toFixed(2)}</div>
        ${
          pay.PAYMENT_QR
            ? `<img src="${pay.PAYMENT_QR}" alt="KHQR" style="max-width:210px;width:100%;margin:10px auto;background:#fff;border-radius:12px;padding:8px;display:block">`
            : `<div style="color:var(--danger);padding:12px">មិនមាន QR — ត្រូវដាក់ KHPAY_API_KEY លើ Render</div>`
        }
        <div style="font-size:0.8rem;color:var(--text-muted);margin-top:8px">Order: <strong style="color:var(--accent)">${o.id}</strong></div>
        <div id="payStatus" style="font-size:0.85rem;color:var(--text-muted);margin-top:8px">រង់ចាំបង់ប្រាក់...</div>
      </div>
      <button class="btn btn-primary btn-block btn-lg" type="button" id="btnPaid" onclick="confirmPaid('${o.id}')">✓ ខ្ញុំបានបង់ហើយ</button>
    `;
    startPoll(o.id);
  } catch (e) {
    alert("Error: " + e.message);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "បញ្ជាទិញឥឡូវនេះ";
    }
  }
}

function startPoll(orderId) {
  if (_poll) clearInterval(_poll);
  let n = 0;
  _poll = setInterval(async () => {
    n++;
    if (n > 90) {
      clearInterval(_poll);
      return;
    }
    try {
      const r = await fetch(API_BASE + "/order/check-payment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: orderId }),
      });
      const data = await r.json();
      const st = document.getElementById("payStatus");
      if (st) st.textContent = "ស្ថានភាព: " + (data.payment_status || "...");
      if (
        data.payment_status === "completed" ||
        ["paid", "processing", "completed", "waiting_fulfill", "delivered"].includes(
          data.order?.status
        )
      ) {
        clearInterval(_poll);
        showDone(data.order, data.message);
      }
    } catch (e) {}
  }, 4000);
}

async function confirmPaid(orderId) {
  const btn = document.getElementById("btnPaid");
  if (btn) {
    btn.disabled = true;
    btn.textContent = "កំពុងផ្ទៀងផ្ទាត់...";
  }
  try {
    const r = await fetch(API_BASE + "/order/confirm-paid", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ order_id: orderId }),
    });
    const data = await r.json();
    if (!data.ok) {
      alert(data.error || "មិនទាន់ទទួលប្រាក់");
      if (btn) {
        btn.disabled = false;
        btn.textContent = "✓ ខ្ញុំបានបង់ហើយ";
      }
      return;
    }
    if (_poll) clearInterval(_poll);
    showDone(data.order, data.message);
  } catch (e) {
    alert(e.message);
    if (btn) {
      btn.disabled = false;
      btn.textContent = "✓ ខ្ញុំបានបង់ហើយ";
    }
  }
}

function showDone(o, message) {
  const map = {
    paid: "បង់រួច",
    processing: "កំពុង deliver...",
    completed: "✓ Delivered",
    waiting_fulfill: "រង់ចាំ admin fulfill",
    delivered: "✓ Delivered",
  };
  showStep(4);
  document.getElementById("successOrderCode").textContent = o.id;
  const box = document.getElementById("stepSuccess");
  if (box) {
    const extra = box.querySelector(".extra-info");
    if (extra) extra.remove();
    const div = document.createElement("div");
    div.className = "extra-info";
    div.style.cssText =
      "text-align:center;font-size:0.9rem;color:var(--text-muted);margin:8px 0 12px";
    div.innerHTML = `
      <div>${o.game_name || ""} · ${o.package_name || ""}</div>
      <div>Player: ${o.player_id || ""}</div>
      <div style="color:var(--success);font-weight:700;margin-top:4px">${map[o.status] || o.status}</div>
      <div style="margin-top:4px">${message || ""}</div>`;
    const codeBox = box.querySelector(".order-code-box");
    if (codeBox) codeBox.after(div);
  }
}

function closeModal() {
  if (_poll) clearInterval(_poll);
  document.getElementById("topupModal")?.classList.remove("open");
  document.body.style.overflow = "";
  // restore stepConfirm for next open - reload page section is heavy; rebuild on next openTopup
  location.hash = "";
}


function applyBranding(s) {
  if (!s) return;
  if (s.SITE_NAME) document.title = s.SITE_NAME + " | Top-up ហ្គេម";
  const note = document.getElementById("heroNote");
  if (note && s.CONTACT_NOTE) note.textContent = s.CONTACT_NOTE;
  const tg = document.getElementById("tgLink");
  if (tg && s.TELEGRAM) tg.href = s.TELEGRAM;
  const tgf = document.getElementById("tgFooter");
  if (tgf && s.TELEGRAM) tgf.href = s.TELEGRAM;
  const logo = s.LOGO_URL || "/static/img/logo.svg";
  document.querySelectorAll("#siteLogo, .logo-img").forEach((el) => { el.src = logo; });
  const banner = document.getElementById("siteBanner");
  if (banner) banner.src = s.BANNER_URL || "/static/img/banner.svg";
  const wrap = document.getElementById("bannerWrap");
  if (wrap && s.BANNER_URL === "hide") wrap.style.display = "none";
  if (s.FAVICON_URL) {
    let link = document.querySelector("link[rel='icon']");
    if (!link) { link = document.createElement("link"); link.rel = "icon"; document.head.appendChild(link); }
    link.href = s.FAVICON_URL;
  }
  const logoText = document.getElementById("siteLogoText");
  if (logoText && s.SITE_NAME) {
    const name = s.SITE_NAME;
    if (name.toLowerCase().includes("topup") || name.toLowerCase().includes("top-up")) {
      const parts = name.replace(/top-?up/i, "|").split("|");
      logoText.innerHTML = (parts[0] || "Angkor") + "<span>TopUp</span>";
    } else {
      logoText.innerHTML = name + "<span></span>";
    }
  }
}

window.openTopup = openTopup;
window.selectPackage = selectPackage;
window.confirmPaid = confirmPaid;
