/* ══════════════════════════════════════════════════════════════════
   Finance Tracker Mini App
   Modullar bot vazifalariga mos:
     🏠 Asosiy      — jamlanma + xarajat tarixi (o'chirish / o'zgartirish)
     ➕ Qo'shish     — kategoriya tanlash + summa kiritish
     📊 Hisobot     — kunlik / haftalik / oylik / yillik
     ⚙️ Kategoriya  — qo'shish / o'zgartirish / o'chirish / yashirish
   ══════════════════════════════════════════════════════════════════ */

const tg = window.Telegram && window.Telegram.WebApp;

const state = {
  categories: [],
  selectedRef: null,
  parts: [""],
  period: "daily",
  historyLimit: 5,
};

/* ── Yordamchilar ─────────────────────────────────────────────────── */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

function fmt(n) {
  const rounded = Math.round(Number(n) || 0);
  return rounded.toLocaleString("uz-UZ").replace(/ /g, " ").replace(/,/g, " ");
}

/** SQLite "YYYY-MM-DD HH:MM:SS" — bot bilan bir xil ko'rinishda (siljitilmaydi) */
function fmtDate(ts, withYear = false) {
  const m = String(ts || "").match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})/);
  if (!m) return "";
  const [, y, mo, d, h, mi] = m;
  return withYear ? `${d}.${mo}.${y} ${h}:${mi}` : `${d}.${mo} ${h}:${mi}`;
}

function fmtDay(iso) {
  const m = String(iso || "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return m ? `${m[3]}.${m[2]}` : iso;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function haptic(type = "light") {
  try {
    if (type === "error" || type === "success" || type === "warning") {
      tg.HapticFeedback.notificationOccurred(type);
    } else {
      tg.HapticFeedback.impactOccurred(type);
    }
  } catch (_) { /* qo'llab-quvvatlanmasa e'tiborsiz */ }
}

let toastTimer = null;
function toast(text, action) {
  const el = $("#toast");
  clearTimeout(toastTimer);
  el.innerHTML = escapeHtml(text);
  if (action) {
    const btn = document.createElement("button");
    btn.className = "link-btn";
    btn.style.marginLeft = "12px";
    btn.textContent = action.label;
    btn.onclick = () => { el.classList.add("hidden"); action.onClick(); };
    el.appendChild(btn);
  }
  el.classList.remove("hidden");
  toastTimer = setTimeout(() => el.classList.add("hidden"), action ? 5000 : 2200);
}

/* ── API ──────────────────────────────────────────────────────────── */

async function api(path, options = {}) {
  const res = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Init-Data": (tg && tg.initData) || "",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let reason = res.statusText;
    try {
      const data = await res.json();
      reason = data.error || reason;
    } catch (_) { /* matnli xato */ }
    throw new Error(reason || "Xatolik yuz berdi");
  }
  return res.json();
}

async function guard(fn) {
  try {
    return await fn();
  } catch (err) {
    haptic("error");
    toast("⚠️ " + (err.message || "Xatolik"));
    return null;
  }
}

/* ── Sheet (pastdan chiquvchi oyna) ───────────────────────────────── */

function openSheet(html) {
  $("#sheet-content").innerHTML = html;
  $("#sheet-backdrop").classList.remove("hidden");
  if (tg && tg.BackButton) {
    tg.BackButton.show();
    tg.BackButton.onClick(closeSheet);
  }
}

function closeSheet() {
  $("#sheet-backdrop").classList.add("hidden");
  $("#sheet-content").innerHTML = "";
  if (tg && tg.BackButton) {
    tg.BackButton.offClick(closeSheet);
    tg.BackButton.hide();
  }
}

$("#sheet-backdrop").addEventListener("click", (e) => {
  if (e.target === $("#sheet-backdrop")) closeSheet();
});

/* ══ 🏠 ASOSIY ═════════════════════════════════════════════════════ */

async function loadHome() {
  const data = await guard(() => api("/api/overview"));
  if (!data) return;

  $("#home-today").textContent = fmt(data.daily.total);
  $("#home-week").textContent = fmt(data.weekly.total);
  $("#home-month").textContent = fmt(data.monthly.total);
  $("#home-week-count").textContent = `${data.weekly.count} ta yozuv`;
  $("#home-month-count").textContent = `${data.monthly.count} ta yozuv`;

  if (state.historyLimit > 5) {
    await loadHistory();
  } else {
    renderHistory(data.recent);
  }
}

async function loadHistory() {
  const data = await guard(() => api(`/api/expenses?limit=${state.historyLimit}`));
  if (data) renderHistory(data.expenses);
}

function renderHistory(expenses) {
  const list = $("#home-list");
  $("#toggle-history").textContent = state.historyLimit > 5 ? "Kamroq" : "Barchasi";

  if (!expenses.length) {
    list.innerHTML = `
      <div class="empty">
        <span class="empty-emoji">🗒️</span>
        Hozircha xarajat yo'q.<br>«➕ Qo'shish» bo'limidan boshlang.
      </div>`;
    return;
  }

  list.innerHTML = expenses.map((e) => `
    <button class="row" data-expense="${e.id}">
      <div class="row-main">
        <div class="row-title">${escapeHtml(e.category)}</div>
        <div class="row-meta">${fmtDate(e.created_at)}</div>
      </div>
      <div class="row-amount">${fmt(e.amount)}</div>
      <div class="row-chevron">›</div>
    </button>`).join("");

  list.querySelectorAll("[data-expense]").forEach((btn) => {
    btn.onclick = () => {
      const exp = expenses.find((e) => String(e.id) === btn.dataset.expense);
      if (exp) openExpenseSheet(exp);
    };
  });
}

$("#toggle-history").onclick = () => {
  state.historyLimit = state.historyLimit > 5 ? 5 : 50;
  haptic();
  loadHome();
};

/* Xarajatni o'zgartirish / o'chirish — botdagi «manage_exp» bilan bir xil */
function openExpenseSheet(exp) {
  haptic();
  openSheet(`
    <h3>${escapeHtml(exp.category)}</h3>
    <div class="sheet-meta">${fmt(exp.amount)} so'm · ${fmtDate(exp.created_at, true)}</div>

    <label class="step-label" for="edit-amount">Yangi summa</label>
    <input class="input" id="edit-amount" inputmode="decimal"
           value="${Math.round(exp.amount)}" autocomplete="off">
    <div class="input-hint">Masalan: 50000, 50k yoki 60000+50000</div>

    <div class="btn-row">
      <button class="btn btn-danger" id="sheet-delete">🗑️ O'chirish</button>
      <button class="btn btn-primary" id="sheet-save">✅ Saqlash</button>
    </div>
    <button class="btn btn-secondary btn-block" id="sheet-cancel">Bekor qilish</button>
  `);

  $("#sheet-cancel").onclick = closeSheet;

  $("#sheet-save").onclick = async () => {
    const amount = parseAmountText($("#edit-amount").value);
    if (!amount) {
      haptic("error");
      toast("⚠️ Noto'g'ri summa");
      return;
    }
    const ok = await guard(() => api(`/api/expenses/${exp.id}`, {
      method: "PATCH",
      body: JSON.stringify({ amount }),
    }));
    if (!ok) return;
    haptic("success");
    closeSheet();
    toast("✅ Summa yangilandi");
    loadHome();
  };

  $("#sheet-delete").onclick = async () => {
    const ok = await guard(() => api(`/api/expenses/${exp.id}`, { method: "DELETE" }));
    if (!ok) return;
    haptic("success");
    closeSheet();
    toast("🗑️ O'chirildi");
    loadHome();
  };
}

/** Botdagi parse_amount bilan bir xil: "50k", "60000+50000" */
function parseAmountText(text) {
  const parts = String(text).trim().toLowerCase().replace(/\s/g, "").replace(/,/g, ".").split("+");
  if (!parts.length || parts.some((p) => !p)) return null;

  let total = 0;
  for (const part of parts) {
    const isK = part.endsWith("k");
    const num = Number(isK ? part.slice(0, -1) : part);
    if (!Number.isFinite(num)) return null;
    total += isK ? num * 1000 : num;
  }
  return total > 0 ? total : null;
}

/* ══ ➕ QO'SHISH ════════════════════════════════════════════════════ */

function renderAddCategories() {
  const visible = state.categories.filter((c) => !c.hidden);
  const grid = $("#add-cats");

  if (!visible.length) {
    grid.innerHTML = `
      <div class="empty" style="grid-column: span 2">
        <span class="empty-emoji">📂</span>
        Ko'rinadigan kategoriya yo'q.<br>«⚙️ Kategoriya» bo'limidan qo'shing.
      </div>`;
    return;
  }

  grid.innerHTML = visible.map((c) => `
    <button class="cat-chip ${c.ref === state.selectedRef ? "selected" : ""}"
            data-ref="${escapeHtml(c.ref)}">${escapeHtml(c.name)}</button>`).join("");

  grid.querySelectorAll("[data-ref]").forEach((btn) => {
    btn.onclick = () => {
      state.selectedRef = btn.dataset.ref;
      haptic();
      renderAddCategories();
      updateAmountView();
    };
  });
}

function currentTotal() {
  return state.parts.reduce((sum, p) => sum + (Number(p) || 0), 0);
}

function updateAmountView() {
  const shown = state.parts.filter((p) => p !== "");
  $("#amount-expr").innerHTML = shown.length > 1
    ? shown.map(fmt).join(" + ")
    : "&nbsp;";
  $("#amount-total").textContent = fmt(currentTotal());
  $("#save-expense").disabled = !(state.selectedRef && currentTotal() > 0);
}

$("#keypad").addEventListener("click", (e) => {
  const btn = e.target.closest(".key");
  if (!btn) return;

  const key = btn.dataset.key;
  const last = state.parts.length - 1;
  haptic();

  if (key === "back") {
    if (state.parts[last]) {
      state.parts[last] = state.parts[last].slice(0, -1);
    } else if (state.parts.length > 1) {
      state.parts.pop();
    }
  } else if (key === "plus") {
    if (state.parts[last]) state.parts.push("");
  } else if (state.parts[last].length + key.length <= 12) {
    if (!(state.parts[last] === "" && key === "000")) {
      state.parts[last] += key;
    }
  }

  updateAmountView();
});

function resetAmount() {
  state.parts = [""];
  updateAmountView();
}

$("#save-expense").onclick = async () => {
  const amount = currentTotal();
  if (!state.selectedRef || amount <= 0) return;

  const data = await guard(() => api("/api/expenses", {
    method: "POST",
    body: JSON.stringify({ ref: state.selectedRef, amount }),
  }));
  if (!data) return;

  haptic("success");
  resetAmount();
  loadHome();

  const created = data.expense;
  toast(`✅ ${fmt(created.amount)} so'm saqlandi`, {
    label: "↩️ Bekor",
    onClick: async () => {
      const ok = await guard(() => api(`/api/expenses/${created.id}`, { method: "DELETE" }));
      if (ok) { haptic("success"); toast("🗑️ Bekor qilindi"); loadHome(); }
    },
  });
};

/* ══ 📊 HISOBOT ════════════════════════════════════════════════════ */

$$("#period-tabs .seg").forEach((btn) => {
  btn.onclick = () => {
    $$("#period-tabs .seg").forEach((b) => b.classList.toggle("active", b === btn));
    state.period = btn.dataset.period;
    haptic();
    loadReport();
  };
});

async function loadReport() {
  const body = $("#report-body");
  body.innerHTML = `<div class="empty">Yuklanmoqda…</div>`;

  const data = await guard(() => api(`/api/report?period=${state.period}`));
  if (!data) { body.innerHTML = `<div class="empty">Yuklab bo'lmadi</div>`; return; }

  if (!data.count) {
    body.innerHTML = `
      <div class="report-range">${fmtDay(data.start_date)} — ${fmtDay(data.end_date)}</div>
      <div class="empty">
        <span class="empty-emoji">📭</span>
        Bu davrda xarajat topilmadi.
      </div>`;
    return;
  }

  body.innerHTML = `
    <div class="card hero-card">
      <div class="hero-label">${escapeHtml(data.title)}</div>
      <div class="hero-figure">${fmt(data.total)}</div>
      <div class="hero-unit">so'm · ${data.count} ta yozuv</div>
    </div>
    <div class="report-range" style="margin-top:10px">
      ${fmtDay(data.start_date)} — ${fmtDay(data.end_date)}
    </div>
    ${renderTrend(data)}
    <div class="chart-title">Kategoriyalar bo'yicha</div>
    <div class="bars">${renderBars(data)}</div>`;

  bindTrend();
}

/* Kunlik trend — bitta seriya, kattalik bo'yicha ustunlar */
function renderTrend(data) {
  if (!data.trend || data.trend.length === 0) return "";

  const points = state.period === "yearly" ? groupByMonth(data.trend) : fillDays(data);
  if (points.length < 2) return "";

  const max = Math.max(...points.map((p) => p.total));
  const cols = points.map((p) => `
    <button class="trend-col ${p.total ? "" : "empty-col"}"
            data-label="${escapeHtml(p.label)}" data-total="${p.total}"
            aria-label="${escapeHtml(p.label)}: ${fmt(p.total)} so'm">
      <div class="trend-bar" style="height:${max ? Math.max((p.total / max) * 100, 2) : 2}%"></div>
    </button>`).join("");

  return `
    <div class="chart-title">${state.period === "yearly" ? "Oylar kesimida" : "Kunlar kesimida"}</div>
    <div class="trend">${cols}</div>
    <div class="trend-axis">
      <span>${escapeHtml(points[0].label)}</span>
      <span>${escapeHtml(points[points.length - 1].label)}</span>
    </div>
    <div class="trend-readout" id="trend-readout">Ustunga bosing — summani ko'rasiz</div>`;
}

/**
 * Bo'sh kunlarni ham ko'rsatish uchun davrni to'liq to'ldiradi.
 * Sana siljib ketmasligi uchun hamma hisob UTC'da bajariladi.
 */
function fillDays(data) {
  const totals = Object.fromEntries(data.trend.map((t) => [t.day, t.total]));
  const points = [];
  const start = new Date(data.start_date + "T00:00:00Z");
  const end = new Date(data.end_date + "T00:00:00Z");

  // Kelajakdagi kunlarni chizmaymiz (masalan oyning qolgan qismi).
  // "Bugun" server sanasidan olinadi — mijoz vaqt mintaqasiga bog'liq emas.
  const today = new Date((data.today || data.end_date) + "T00:00:00Z");
  const stop = end < today ? end : today;

  for (let d = new Date(start); d <= stop; d.setUTCDate(d.getUTCDate() + 1)) {
    const iso = d.toISOString().slice(0, 10);
    points.push({ label: fmtDay(iso), total: totals[iso] || 0 });
  }
  return points;
}

const MONTHS = ["Yan", "Fev", "Mar", "Apr", "May", "Iyun", "Iyul", "Avg", "Sen", "Okt", "Noy", "Dek"];

function groupByMonth(trend) {
  const totals = new Array(12).fill(0);
  trend.forEach((t) => {
    const month = Number(String(t.day).slice(5, 7)) - 1;
    if (month >= 0 && month < 12) totals[month] += t.total;
  });
  return totals.map((total, i) => ({ label: MONTHS[i], total }));
}

function bindTrend() {
  const readout = $("#trend-readout");
  if (!readout) return;

  $$(".trend-col").forEach((col) => {
    col.onclick = () => {
      $$(".trend-col").forEach((c) => c.classList.toggle("active", c === col));
      readout.innerHTML = `${escapeHtml(col.dataset.label)} — <b>${fmt(col.dataset.total)} so'm</b>`;
      haptic();
    };
  });
}

/* Kategoriya ustunlari — nom va summa har doim ko'rinadi (rangga tayanmaydi) */
function renderBars(data) {
  const max = Math.max(...data.categories.map((c) => c.total));
  return data.categories.map((c) => {
    const percent = data.total > 0 ? (c.total / data.total) * 100 : 0;
    return `
      <div class="bar-item">
        <div class="bar-head">
          <span class="bar-name">${escapeHtml(c.category)}</span>
          <span class="bar-val">${fmt(c.total)} so'm</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" style="width:${max ? (c.total / max) * 100 : 0}%"></div>
        </div>
        <div class="bar-sub">${percent.toFixed(0)}% · ${c.count} ta</div>
      </div>`;
  }).join("");
}

/* ══ ⚙️ KATEGORIYALAR ══════════════════════════════════════════════ */

async function loadCategories() {
  const data = await guard(() => api("/api/categories"));
  if (data) applyCategories(data.categories);
}

function applyCategories(categories) {
  state.categories = categories;
  if (state.selectedRef && !categories.some((c) => c.ref === state.selectedRef && !c.hidden)) {
    state.selectedRef = null;
  }
  renderCategoriesList();
  renderAddCategories();
  updateAmountView();
}

function renderCategoriesList() {
  const list = $("#cats-list");

  list.innerHTML = state.categories.map((c) => `
    <button class="row ${c.hidden ? "is-hidden" : ""}" data-ref="${escapeHtml(c.ref)}">
      <div class="row-main">
        <div class="row-title">${escapeHtml(c.name)}</div>
        <div class="row-meta">${c.custom ? "✏️ Qo'shilgan" : c.hidden ? "🚫 Yashirilgan" : "Standart"}</div>
      </div>
      <div class="row-chevron">›</div>
    </button>`).join("");

  list.querySelectorAll("[data-ref]").forEach((btn) => {
    btn.onclick = () => {
      const cat = state.categories.find((c) => c.ref === btn.dataset.ref);
      if (cat) openCategorySheet(cat);
    };
  });
}

function openCategorySheet(cat) {
  haptic();

  const actions = cat.custom
    ? `<div class="btn-row">
         <button class="btn btn-danger" id="cat-delete">🗑️ O'chirish</button>
         <button class="btn btn-primary" id="cat-rename">✏️ Nomni saqlash</button>
       </div>`
    : `<button class="btn ${cat.hidden ? "btn-primary" : "btn-secondary"} btn-block" id="cat-toggle">
         ${cat.hidden ? "👁️ Ko'rsatish" : "🚫 Yashirish"}
       </button>`;

  openSheet(`
    <h3>${escapeHtml(cat.name)}</h3>
    <div class="sheet-meta">${cat.custom ? "Siz qo'shgan kategoriya" : "Standart kategoriya"}</div>
    ${cat.custom ? `
      <label class="step-label" for="cat-name">Kategoriya nomi</label>
      <input class="input" id="cat-name" value="${escapeHtml(cat.name)}" maxlength="40" autocomplete="off">
      <div class="input-hint">2–40 ta belgi</div>` : ""}
    ${actions}
    <button class="btn btn-secondary btn-block" id="cat-cancel">Yopish</button>
  `);

  $("#cat-cancel").onclick = closeSheet;

  const toggleBtn = $("#cat-toggle");
  if (toggleBtn) {
    toggleBtn.onclick = async () => {
      const data = await guard(() => api("/api/categories/visibility", {
        method: "POST",
        body: JSON.stringify({ ref: cat.ref, hidden: !cat.hidden }),
      }));
      if (!data) return;
      haptic("success");
      closeSheet();
      applyCategories(data.categories);
      toast(cat.hidden ? "👁️ Ko'rsatildi" : "🚫 Yashirildi");
    };
  }

  const renameBtn = $("#cat-rename");
  if (renameBtn) {
    renameBtn.onclick = async () => {
      const name = $("#cat-name").value.trim();
      if (name.length < 2 || name.length > 40) {
        haptic("error");
        toast("⚠️ Nom 2–40 ta belgi bo'lsin");
        return;
      }
      const data = await guard(() => api(`/api/categories/${cat.ref.slice(2)}`, {
        method: "PATCH",
        body: JSON.stringify({ name }),
      }));
      if (!data) return;
      haptic("success");
      closeSheet();
      applyCategories(data.categories);
      toast("✅ Saqlandi");
    };
  }

  const deleteBtn = $("#cat-delete");
  if (deleteBtn) {
    deleteBtn.onclick = async () => {
      const data = await guard(() => api(`/api/categories/${cat.ref.slice(2)}`, { method: "DELETE" }));
      if (!data) return;
      haptic("success");
      closeSheet();
      applyCategories(data.categories);
      toast("🗑️ O'chirildi");
    };
  }
}

$("#add-cat-btn").onclick = () => {
  haptic();
  openSheet(`
    <h3>➕ Yangi kategoriya</h3>
    <div class="sheet-meta">Masalan: 🏋️ Fitness yoki 📚 Kitoblar</div>
    <input class="input" id="new-cat-name" placeholder="Kategoriya nomi" maxlength="40" autocomplete="off">
    <div class="input-hint">2–40 ta belgi</div>
    <button class="btn btn-primary btn-block" id="new-cat-save">✅ Qo'shish</button>
    <button class="btn btn-secondary btn-block" id="new-cat-cancel">Bekor qilish</button>
  `);

  $("#new-cat-name").focus();
  $("#new-cat-cancel").onclick = closeSheet;

  $("#new-cat-save").onclick = async () => {
    const name = $("#new-cat-name").value.trim();
    if (name.length < 2 || name.length > 40) {
      haptic("error");
      toast("⚠️ Nom 2–40 ta belgi bo'lsin");
      return;
    }
    const data = await guard(() => api("/api/categories", {
      method: "POST",
      body: JSON.stringify({ name }),
    }));
    if (!data) return;
    haptic("success");
    closeSheet();
    applyCategories(data.categories);
    toast("✅ Kategoriya qo'shildi");
  };
};

/* ══ Navigatsiya ═══════════════════════════════════════════════════ */

function showTab(name) {
  $$(".page").forEach((p) => p.classList.toggle("hidden", p.dataset.page !== name));
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  window.scrollTo(0, 0);

  if (name === "home") loadHome();
  if (name === "report") loadReport();
}

$$(".tab").forEach((tab) => {
  tab.onclick = () => { haptic(); showTab(tab.dataset.tab); };
});

/* ══ Ishga tushirish ═══════════════════════════════════════════════ */

function applyTheme() {
  const scheme = (tg && tg.colorScheme) || "light";
  document.documentElement.setAttribute("data-theme", scheme);
  const plane = getComputedStyle(document.documentElement).getPropertyValue("--plane").trim();
  try {
    tg.setHeaderColor(plane);
    tg.setBackgroundColor(plane);
  } catch (_) { /* eski mijozlar */ }
}

async function init() {
  if (!tg || !tg.initData) {
    $("#loader").classList.add("hidden");
    $("#gate").classList.remove("hidden");
    return;
  }

  tg.ready();
  tg.expand();
  applyTheme();
  tg.onEvent("themeChanged", applyTheme);

  const me = await guard(() => api("/api/me"));
  if (!me) {
    $("#loader").classList.add("hidden");
    $("#gate").classList.remove("hidden");
    return;
  }

  $("#user-name").textContent = me.first_name || "Do'stim";
  if (me.photo_url) {
    $("#avatar").innerHTML = `<img src="${escapeHtml(me.photo_url)}" alt="">`;
  }

  await loadCategories();
  await loadHome();

  $("#loader").classList.add("hidden");
  $("#app").classList.remove("hidden");
}

init();
