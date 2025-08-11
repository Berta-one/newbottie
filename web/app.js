/* Bottie Netlify Dashboard */
const $ = (sel) => document.querySelector(sel);
const apiInput = $("#apiBase");
const saveBtn = $("#saveApi");

function getApiBase() {
  // priority: input → localStorage → ?api= query → default placeholder
  const urlParam = new URLSearchParams(location.search).get("api");
  if (urlParam) return urlParam;
  const saved = localStorage.getItem("bottie_api");
  if (saved) return saved;
  return "https://bottie-api.onrender.com"; // change if needed
}

function setApiBase(v) {
  localStorage.setItem("bottie_api", v);
  apiInput.value = v;
}

let API_BASE = getApiBase();
setApiBase(API_BASE);
saveBtn.addEventListener("click", () => {
  const v = apiInput.value.trim();
  if (!v) return;
  setApiBase(v);
  API_BASE = v;
  ping(); // refresh immediately
});

/* Charts */
let equityChart;
function initChart() {
  const ctx = document.getElementById("equityChart").getContext("2d");
  equityChart = new Chart(ctx, {
    type: "line",
    data: { labels: [], datasets: [{
      label: "Equity",
      data: [],
      fill: false,
      borderWidth: 2,
      tension: 0.25
    }]},
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { display: false }, y: { ticks: { display: true } } }
    }
  });
}
initChart();

/* UI helpers */
function setHealth(ok, ts, quantum) {
  $("#health-status").textContent = ok ? "OK" : "DOWN";
  $("#health-status").style.color = ok ? "#66e0a3" : "#ef6f6c";
  $("#health-time").textContent = ts ? new Date(ts * 1000).toLocaleTimeString() : "—";
  $("#health-quantum").textContent = quantum || "—";
}

function setEquity(eq) {
  $("#equity").textContent = typeof eq === "number" ? eq.toFixed(2) : "—";
  const ds = equityChart.data.datasets[0];
  const labels = equityChart.data.labels;
  const now = new Date().toLocaleTimeString();
  if (typeof eq === "number") {
    labels.push(now);
    ds.data.push(eq);
    if (labels.length > 120) { labels.shift(); ds.data.shift(); }
    equityChart.update();
  }
}

function setPositions(positions) {
  const tbody = $("#positionsTable tbody");
  tbody.innerHTML = "";
  if (!positions || !Object.keys(positions).length) {
    tbody.innerHTML = `<tr><td colspan="3" style="color:#9bb0bf">No positions</td></tr>`;
    return;
  }
  for (const [sym, p] of Object.entries(positions)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${sym}</td><td>${(+p.qty).toFixed(6)}</td><td>${(+p.avg_px).toFixed(4)}</td>`;
    tbody.appendChild(tr);
  }
}

function setSignals(signals) {
  const tbody = $("#signalsTable tbody");
  tbody.innerHTML = "";
  if (!signals || !signals.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:#9bb0bf">No signals yet</td></tr>`;
    return;
  }
  const last = signals.slice(-50).reverse();
  for (const s of last) {
    const t = s.t ? new Date(s.t * 1000).toLocaleTimeString() : "–";
    const conf = (s.conf != null) ? (+s.conf).toFixed(3) : "–";
    const tr = document.createElement("tr");
    let color = "#9bb0bf";
    if (s.signal === "BUY") color = "#66e0a3";
    if (s.signal === "SELL") color = "#ef6f6c";
    tr.innerHTML = `<td>${t}</td><td>${s.symbol || "–"}</td><td style="color:${color};font-weight:700">${s.signal || "–"}</td><td>${conf}</td>`;
    tbody.appendChild(tr);
  }
}

async function fetchJSON(path) {
  const res = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

/* Polling */
async function ping() {
  try {
    const health = await fetchJSON("/health");
    const q = health.quantum ? `${health.quantum.kind}:${health.quantum.backend}` : "—";
    setHealth(!!health.ok, health.time, q);
  } catch (e) {
    setHealth(false, null, null);
  }

  try {
    const status = await fetchJSON("/status");
    setEquity(status.equity);
    setPositions(status.positions);
    setSignals(status.last_signals || status.signals);
  } catch (e) {
    console.warn("status error:", e.message);
  }

  try {
    const logs = await fetchJSON("/logs/last");
    const text = (logs.logs || []).join("\n");
    $("#logsView").textContent = text || "—";
  } catch (e) {
    // ignore
  }
}

setInterval(ping, 2000);
ping();