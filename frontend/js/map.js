/**
 * Travel Planner — Frontend JS
 * Consumes ONLY the internal Airport Service and Itinerary Service.
 * Never calls API Colombia directly.
 */

const CONFIG = {
  AIRPORT_SERVICE:   "http://localhost:8001",
  ITINERARY_SERVICE: "http://localhost:8002",
};

// ── State ─────────────────────────────────────────────────────────────────────
let allAirports    = [];
let allItineraries = [];

// ── API calls ─────────────────────────────────────────────────────────────────
async function fetchAirports() {
  const res = await fetch(`${CONFIG.AIRPORT_SERVICE}/airports`);
  if (!res.ok) throw new Error(`Airport Service: ${res.status}`);
  return res.json();
}

async function fetchPlotlyData() {
  const res = await fetch(`${CONFIG.AIRPORT_SERVICE}/airports/plotly`);
  if (!res.ok) throw new Error(`Plotly endpoint: ${res.status}`);
  return res.json();
}

async function fetchItineraries() {
  const res = await fetch(`${CONFIG.ITINERARY_SERVICE}/itineraries`);
  if (!res.ok) throw new Error(`Itinerary Service: ${res.status}`);
  return res.json();
}

async function createItinerary(payload) {
  const res = await fetch(`${CONFIG.ITINERARY_SERVICE}/itineraries`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Error creating itinerary");
  return data;
}

async function deleteItinerary(id) {
  const res = await fetch(`${CONFIG.ITINERARY_SERVICE}/itineraries/${id}`, { method: "DELETE" });
  if (res.status !== 204 && !res.ok) throw new Error("Error deleting itinerary");
}

// ── Map ───────────────────────────────────────────────────────────────────────
async function renderMap() {
  const mapEl = document.getElementById("airport-map");
  mapEl.innerHTML = '<div class="loader">⏳ Cargando aeropuertos desde Airport Service…</div>';

  try {
    const airports = await fetchPlotlyData();
    allAirports    = await fetchAirports();

    const trace = {
      type: "scattergeo",
      mode: "markers",
      lat:  airports.map(a => a.latitud),
      lon:  airports.map(a => a.longitud),
      text: airports.map(a => a.codigo),
      customdata: airports.map(a => [a.nombre, a.ciudad, a.codigo]),
      hovertemplate:
        "<b>%{customdata[0]}</b><br>" +
        "Ciudad: %{customdata[1]}<br>" +
        "IATA: %{customdata[2]}<br>" +
        "Lat: %{lat:.4f} | Lon: %{lon:.4f}<extra></extra>",
      marker: {
        size: 10,
        color: "#2e75b6",
        symbol: "circle",
        line: { width: 1, color: "#1f3864" },
        opacity: 0.85,
      },
    };

    const layout = {
      geo: {
        scope: "south america",
        showland: true,       landcolor: "#eaf3fb",
        showocean: true,      oceancolor: "#c8dff5",
        showcountries: true,  countrycolor: "#aaaaaa",
        showcoastlines: true, coastlinecolor: "#888888",
        showlakes: true,      lakecolor: "#c8dff5",
        center: { lat: 4.5, lon: -74.0 },
        projection: { type: "mercator", scale: 4.5 },
        bgcolor: "#f0f4f8",
      },
      margin: { t: 10, b: 10, l: 0, r: 0 },
      paper_bgcolor: "white",
      showlegend: false,
    };

    mapEl.innerHTML = "";
    Plotly.newPlot("airport-map", [trace], layout, {
      responsive: true,
      displayModeBar: false,
    });

    // Populate selects
    populateAirportSelects(allAirports);
    updateAirportCount(airports.length);
  } catch (err) {
    mapEl.innerHTML = `<div style="padding:30px;color:#c53030;text-align:center">
      ❌ Error cargando mapa: ${err.message}<br>
      <small>¿Está corriendo el Airport Service en ${CONFIG.AIRPORT_SERVICE}?</small>
    </div>`;
    setStatus("airport", false);
  }
}

function populateAirportSelects(airports) {
  const opts = airports
    .sort((a, b) => a.city.localeCompare(b.city))
    .map(a => `<option value="${a.id}">${a.city} — ${a.name} (${a.iata_code || a.id})</option>`)
    .join("");
  document.getElementById("dep-airport").innerHTML  = '<option value="">Seleccionar…</option>' + opts;
  document.getElementById("arr-airport").innerHTML  = '<option value="">Seleccionar…</option>' + opts;
}

function updateAirportCount(n) {
  const el = document.getElementById("airport-count");
  if (el) el.textContent = `${n} aeropuertos`;
}

// ── Itineraries ───────────────────────────────────────────────────────────────
async function loadItineraries() {
  const listEl = document.getElementById("itinerary-list");
  listEl.innerHTML = '<div class="loader">⏳ Cargando itinerarios…</div>';
  try {
    allItineraries = await fetchItineraries();
    renderItineraryList(allItineraries);
    setStatus("itinerary", true);
  } catch (err) {
    listEl.innerHTML = `<div style="color:#c53030;font-size:0.85rem">
      ❌ ${err.message}<br><small>¿Está corriendo el Itinerary Service en ${CONFIG.ITINERARY_SERVICE}?</small>
    </div>`;
    setStatus("itinerary", false);
  }
}

function renderItineraryList(items) {
  const listEl = document.getElementById("itinerary-list");
  document.getElementById("itin-count").textContent = `${items.length} itinerario${items.length !== 1 ? "s" : ""}`;
  if (!items.length) {
    listEl.innerHTML = '<div id="empty-state">Sin itinerarios. ¡Crea el primero! ✈️</div>';
    return;
  }
  listEl.innerHTML = items.map(it => `
    <div class="itinerary-card" id="card-${it.id}">
      <div class="card-header">
        <div>
          <div class="card-user">👤 ${escapeHtml(it.user_name)}</div>
          <div class="card-date">📅 ${it.travel_date}</div>
        </div>
        <div class="card-actions">
          <button class="btn-danger btn-sm" onclick="handleDelete(${it.id})">🗑 Eliminar</button>
        </div>
      </div>
      <div class="card-route">✈️ Aeropuerto #${it.departure_airport_id} → Aeropuerto #${it.arrival_airport_id}</div>
      <div class="card-duration">⏱ ${it.duration_minutes} minutos</div>
    </div>
  `).join("");
}

// ── Form ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("itinerary-form")
    .addEventListener("submit", handleFormSubmit);
});

async function handleFormSubmit(e) {
  e.preventDefault();
  const msgEl = document.getElementById("form-message");
  msgEl.style.display = "none";

  const payload = {
    user_name:            document.getElementById("user-name").value.trim(),
    departure_airport_id: document.getElementById("dep-airport").value,
    arrival_airport_id:   document.getElementById("arr-airport").value,
    travel_date:          document.getElementById("travel-date").value,
    duration_minutes:     parseInt(document.getElementById("duration").value, 10),
  };

  try {
    await createItinerary(payload);
    showMessage(msgEl, "✅ Itinerario creado exitosamente.", "success");
    e.target.reset();
    await loadItineraries();
  } catch (err) {
    showMessage(msgEl, `❌ ${err.message}`, "error");
  }
}

async function handleDelete(id) {
  if (!confirm(`¿Eliminar itinerario #${id}?`)) return;
  try {
    await deleteItinerary(id);
    document.getElementById(`card-${id}`)?.remove();
    allItineraries = allItineraries.filter(i => i.id !== id);
    document.getElementById("itin-count").textContent =
      `${allItineraries.length} itinerario${allItineraries.length !== 1 ? "s" : ""}`;
    if (!allItineraries.length) {
      document.getElementById("itinerary-list").innerHTML =
        '<div id="empty-state">Sin itinerarios. ¡Crea el primero! ✈️</div>';
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

// ── Status indicators ─────────────────────────────────────────────────────────
function setStatus(service, ok) {
  const el = document.getElementById(`status-${service}`);
  if (!el) return;
  el.querySelector(".status-dot").className = `status-dot ${ok ? "dot-green" : "dot-red"}`;
  el.querySelector(".status-text").textContent = ok ? "online" : "offline";
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function showMessage(el, text, type) {
  el.textContent = text;
  el.className = type === "success" ? "msg-success" : "msg-error";
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 5000);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

async function checkServices() {
  for (const [svc, url] of [["airport", CONFIG.AIRPORT_SERVICE], ["itinerary", CONFIG.ITINERARY_SERVICE]]) {
    try {
      const r = await fetch(`${url}/health`, { signal: AbortSignal.timeout(3000) });
      setStatus(svc, r.ok);
    } catch { setStatus(svc, false); }
  }
}

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Set min date for travel_date
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("travel-date").min = today;

  await checkServices();
  await renderMap();
  await loadItineraries();
});
