// app.js — Smart Grocery front-end for FastAPI at http://127.0.0.1:8000

// ---------- Config ----------
const API = "http://127.0.0.1:8000";

// ---------- Tiny helpers ----------
const $ = s => document.querySelector(s);
const $$ = s => Array.from(document.querySelectorAll(s));
// FIXED: closing paren so replace() compiles
const esc = s =>
  String(s ?? "").replace(/[&<>"']/g, m => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[m]
  ));
const dollars = x => `$${(Number(x) || 0).toFixed(2)}`;
const byId = id => document.getElementById(id);

// ---------- State ----------
let PANTRY = [];                 // array of strings
let WEEK_PAYLOAD = null;         // full server response after planning

// ---------- Tabs ----------
function initTabs() {
  const screens = ["onboard", "planner", "shop"];
  $$(".tabs .tab").forEach(btn => {
    btn.addEventListener("click", () => {
      $$(".tabs .tab").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      screens.forEach(sc => byId(`screen-${sc}`).classList.add("hidden"));
      const target = btn.dataset.screen;
      byId(`screen-${target}`).classList.remove("hidden");
    });
  });
}

// ---------- Pantry chips editor ----------
function renderPantryChips() {
  const wrap = byId("pantryChips");
  if (!wrap) return;

  if (!PANTRY.length) {
    wrap.innerHTML = `<div class="hint">No items yet — add a few (e.g., eggs, pasta, olive oil)</div>`;
    return;
  }
  wrap.innerHTML = PANTRY.map((name, i) => `
    <span class="chip">
      ${esc(name)}
      <button class="chip-x" data-i="${i}" aria-label="remove ${esc(name)}">×</button>
    </span>
  `).join("");

  wrap.querySelectorAll(".chip-x").forEach(btn => {
    btn.onclick = () => {
      const idx = Number(btn.dataset.i);
      PANTRY.splice(idx, 1);
      renderPantryChips();
    };
  });
}

function addPantryItemsFromInput() {
  const inp = byId("addInput");
  if (!inp) return;
  const v = (inp.value || "").trim();
  if (!v) return;
  const items = v.split(",")
    .map(s => s.trim())
    .filter(Boolean)
    .map(s => s.toLowerCase());
  for (const it of items) {
    if (!PANTRY.includes(it)) PANTRY.push(it);
  }
  inp.value = "";
  renderPantryChips();
}

// Save pantry to server (flexible payload supported by your API)
async function savePantry() {
  const saveStatus = byId("saveStatus");
  try {
    if (saveStatus) saveStatus.textContent = "Saving…";
    const res = await fetch(`${API}/pantry`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(PANTRY)
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if (saveStatus) {
      saveStatus.textContent = `Saved (${data.size})`;
      setTimeout(() => saveStatus.textContent = "", 1200);
    }
    localStorage.setItem("sg_pantry", JSON.stringify(PANTRY));
  } catch (err) {
    console.error(err);
    if (saveStatus) saveStatus.textContent = "Save failed";
  }
}

// Load pantry from server on boot (fallback to localStorage)
async function loadPantry() {
  try {
    const res = await fetch(`${API}/pantry`);
    if (res.ok) {
      const data = await res.json();
      const items = Array.isArray(data.items) ? data.items : [];
      PANTRY = items.map(s => String(s).toLowerCase());
      renderPantryChips();
      return;
    }
  } catch (_) { /* ignore */ }

  // fallback: local cache
  try {
    const cached = JSON.parse(localStorage.getItem("sg_pantry") || "[]");
    if (Array.isArray(cached)) {
      PANTRY = cached.map(s => String(s).toLowerCase());
      renderPantryChips();
    }
  } catch (_) { /* ignore */ }
}

// ---------- Health check ----------
async function ping() {
  const el = byId("pingStatus");
  if (el) el.textContent = "Checking…";
  try {
    const res = await fetch(`${API}/health`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    if (el) {
      el.textContent = `OK • ${data.pantry_size} items`;
      setTimeout(() => el.textContent = "", 1200);
    }
  } catch (err) {
    console.error(err);
    if (el) el.textContent = "No response";
  }
}

// ---------- Week planning ----------
async function handlePlanWeek() {
  const status = byId("planStatus");
  if (status) status.textContent = "Planning…";

  await savePantry(); // keep backend in sync

  const payload = {
    budget: Number(byId("budgetWeek")?.value || 0),
    max_time: Number(byId("maxTime")?.value || 0),
    k_new: Number(byId("rmrK")?.value || 0),
    max_calories_per_meal: Number(byId("maxCal")?.value || 0),
    strategy: byId("strategy")?.value || "knapsack_max_recipes",
  };

  try {
    const res = await fetch(`${API}/plan-week-server`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    WEEK_PAYLOAD = data;

    const days = (data.week_plan || []).slice(0, 7);
    renderWeek(days);
    renderMetrics(data.metrics || {});
    renderShopList(data.grocery_list || []);

    const any = days.some(Boolean);
    if (status) {
      status.textContent = any ? "Planned!" : "No recipes found. Try raising budget/time or add pantry items.";
      setTimeout(() => status.textContent = "", 2000);
    }
  } catch (err) {
    console.error("plan-week-server failed:", err);
    if (status) status.textContent = "Error planning.";
  }
}

function renderWeek(days) {
  const grid = byId("weekGrid");
  if (!grid) return;
  const names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  grid.innerHTML = (days || []).map((r, i) => {
    if (!r) {
      return `
        <div class="day" data-idx="${i}">
          <h4>${names[i]}</h4>
          <div class="meta">No recipe</div>
        </div>`;
    }
    const missing = (r.missing || []).map(m => m.name).join(", ");
    const existing = (r.existing || []).join(", ");
    return `
      <div class="day clickable" data-idx="${i}">
        <h4>${names[i]}</h4>
        <div class="name">${esc(r.name)}</div>
        <div class="meta">time ${esc(r.time_min)} min • ${esc(r.calories)} cal • ${dollars(r.est_total_cost)}</div>
        <div class="meta"><b>missing:</b> ${esc(missing || "-")}</div>
        <div class="meta"><b>have:</b> ${esc(existing || "-")}</div>
        <div class="hint">Click for full recipe →</div>
      </div>`;
  }).join("");

  grid.querySelectorAll(".day.clickable").forEach(card => {
    card.onclick = () => {
      const idx = Number(card.dataset.idx);
      const r = (WEEK_PAYLOAD?.week_plan || [])[idx];
      if (r) openRecipeModal(r);
    };
  });
}

function renderMetrics(m) {
  const card = byId("metricsCard");
  const box = byId("metrics");
  if (!box || !card) return;

  box.innerHTML = `
    <div>Strategy: <b>${esc(m.strategy || "-")}</b></div>
    <div>Budget: ${dollars(m.target_budget)}</div>
    <div>Total spend (chosen): ${dollars(m.total_spend)}</div>
    <div>RMR@k (all/chosen): ${esc(m.rmr_percent_at_k_all)}% / ${esc(m.rmr_percent_at_k_chosen)}%</div>
  `;
  card.classList.remove("hidden");
}

function renderShopList(items) {
  const tbl = byId("shopTable");
  if (!tbl) return;
  tbl.innerHTML = `<tr><th>Item</th><th>Est. Price</th></tr>` +
    (items || []).map(it => `<tr><td>${esc(it.name)}</td><td>${dollars(it.est_price)}</td></tr>`).join("");
}

// ---------- Modal ----------
function openRecipeModal(r) {
  byId("modalTitle").textContent = r.name || "";
  byId("modalMeta").textContent = `time ${r.time_min} min • ${r.calories} cal • ${dollars(r.est_total_cost)}`;
  byId("modalIngredients").innerHTML = (r.ingredients || []).map(x => `<li>${esc(x)}</li>`).join("");
  byId("modalInstructions").innerHTML = (r.instructions || []).map(x => `<li>${esc(x)}</li>`).join("");
  byId("recipeModal").classList.remove("hidden");
}
byId("modalClose").onclick = () => byId("recipeModal").classList.add("hidden");
byId("recipeModal").addEventListener("click", e => {
  if (e.target.id === "recipeModal") byId("recipeModal").classList.add("hidden");
});

// ---------- Downloads ----------
function download(filename, text) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

function downloadShopCsv() {
  const items = WEEK_PAYLOAD?.grocery_list || [];
  const rows = [["item", "est_price"], ...items.map(it => [it.name, String(it.est_price)])];
  const csv = rows.map(r => r.map(x => {
    const s = String(x ?? "");
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }).join(",")).join("\n");
  download("shopping_list.csv", csv);
}

function downloadPlanJson() {
  download("week_plan.json", JSON.stringify(WEEK_PAYLOAD || {}, null, 2));
}

// ---------- Wire up ----------
function initEvents() {
  byId("pingBtn")?.addEventListener("click", ping);
  byId("addBtn")?.addEventListener("click", addPantryItemsFromInput);
  byId("addInput")?.addEventListener("keydown", e => {
    if (e.key === "Enter") addPantryItemsFromInput();
  });
  byId("savePantryBtn")?.addEventListener("click", savePantry);
  byId("planWeekBtn")?.addEventListener("click", handlePlanWeek);
  byId("dlShopCsv")?.addEventListener("click", downloadShopCsv);
  byId("dlPlanJson")?.addEventListener("click", downloadPlanJson);
}

// ---------- Boot ----------
window.addEventListener("DOMContentLoaded", async () => {
  initTabs();
  initEvents();
  await loadPantry();
  // optional: await ping();
});
