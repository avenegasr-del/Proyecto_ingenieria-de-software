/**
 * AeroRoutes — Frontend JS
 * Conserva las mismas funciones de Airport Service e Itinerary Service.
 */

const CONFIG = {
  AIRPORT_SERVICE:   "http://127.0.0.1:8001",
  ITINERARY_SERVICE: "http://127.0.0.1:8002",
};

const COLOMBIA_BOUNDS = [[-4.5, -82.5], [13.8, -66.2]];
const COLOMBIA_CENTER = [4.5, -74.0];
const OSM_TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const TILE_ATTRIBUTION = '© OpenStreetMap contributors';

let allAirports = [];
let allItineraries = [];
window.selectedItineraryId = null;
window.leafletMap = null;
window.leafletLayerGroup = null;
window.activeTileLayer = null;
window.airportServiceReady = false;
window.itineraryServiceReady = false;
window.serviceAvailabilityChecked = false;

async function fetchAirports() {
  const res = await fetch(`${CONFIG.AIRPORT_SERVICE}/airports`);
  if (!res.ok) throw new Error(`Airport Service: ${res.status}`);
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
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errorText = parseApiError(data.detail) || parseApiError(data) || "Error creando itinerario";
    throw new Error(errorText);
  }
  return data;
}

async function deleteItinerary(id) {
  const res = await fetch(`${CONFIG.ITINERARY_SERVICE}/itineraries/${id}`, { method: "DELETE" });
  if (res.status !== 204 && !res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(parseApiError(data.detail) || "Error deleting itinerary");
  }
}

function parseApiError(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map(err => err.msg || err.message || JSON.stringify(err)).join("; ");
  }
  if (typeof detail === "object") {
    return detail.message || detail.detail || JSON.stringify(detail);
  }
  return String(detail);
}

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : NaN;
}

function getAirportLatitude(airport) {
  return toNumber(airport.latitud ?? airport.latitude ?? airport.lat);
}

function getAirportLongitude(airport) {
  return toNumber(airport.longitud ?? airport.longitude ?? airport.lon ?? airport.lng);
}

function getAirportCode(airport) {
  return airport.codigo || airport.iata_code || airport.id;
}

function getAirportName(airport) {
  return airport.nombre || airport.name || airport.id;
}

function getAirportCity(airport) {
  return airport.ciudad || airport.city || 'Sin ciudad';
}

const LEAFLET_CDN_SCRIPTS = [
  "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
  "https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js",
];

async function loadScript(src) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = src;
    script.crossOrigin = "";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script ${src}`));
    document.head.appendChild(script);
  });
}

async function ensureLeafletLoaded() {
  if (typeof L !== "undefined") {
    return;
  }

  const existing = document.querySelector('script[src*="leaflet.js"]');
  if (existing) {
    await new Promise((resolve, reject) => {
      if (existing.readyState === "complete" || existing.readyState === "loaded" || existing.complete) {
        return typeof L !== "undefined" ? resolve() : reject(new Error("Leaflet script present but L not defined"));
      }
      existing.addEventListener("load", () => {
        typeof L !== "undefined" ? resolve() : reject(new Error("Leaflet loaded but L is still undefined"));
      });
      existing.addEventListener("error", () => reject(new Error("Failed to load existing Leaflet script")));
    });
    if (typeof L !== "undefined") return;
  }

  for (const src of LEAFLET_CDN_SCRIPTS) {
    try {
      await loadScript(src);
      if (typeof L !== "undefined") return;
    } catch (err) {
      console.warn(err.message);
    }
  }

  throw new Error("No se pudo cargar Leaflet desde los CDNs disponibles.");
}

function computeGreatCircleDistance(lat1, lon1, lat2, lon2) {
  const aLat = toNumber(lat1);
  const aLon = toNumber(lon1);
  const bLat = toNumber(lat2);
  const bLon = toNumber(lon2);
  if (!Number.isFinite(aLat) || !Number.isFinite(aLon) || !Number.isFinite(bLat) || !Number.isFinite(bLon)) {
    return NaN;
  }
  const rad = Math.PI / 180;
  const dLat = (bLat - aLat) * rad;
  const dLon = (bLon - aLon) * rad;
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * rad) * Math.cos(bLat * rad) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return 6371 * c;
}

function computeDurationMinutes(depAirport, arrAirport) {
  const distanceKm = computeGreatCircleDistance(
    getAirportLatitude(depAirport),
    getAirportLongitude(depAirport),
    getAirportLatitude(arrAirport),
    getAirportLongitude(arrAirport),
  );
  if (!Number.isFinite(distanceKm)) {
    return NaN;
  }
  const cruiseSpeedKmh = 820;
  return Math.max(25, Math.round((distanceKm / cruiseSpeedKmh) * 60 + 15));
}

function getAirportById(id) {
  return allAirports.find(a => String(a.id) === String(id)) || null;
}

function airportLabel(airport) {
  if (!airport) return "?";
  return `${getAirportCity(airport)} — ${getAirportName(airport)} (${getAirportCode(airport)})`;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function setStatus(service, ok) {
  const el = document.getElementById(`status-${service}`);
  if (!el) return;
  if (service === "airport") window.airportServiceReady = ok;
  if (service === "itinerary") window.itineraryServiceReady = ok;
  el.querySelector(".status-dot").className = `status-dot ${ok ? "dot-green" : "dot-red"}`;
  el.querySelector(".status-text").textContent = ok ? "online" : "offline";
  window.serviceAvailabilityChecked = true;
  updateFormAvailability();
}

function showMessage(el, text, type) {
  el.textContent = text;
  el.className = type === "success" ? "form-message success" : "form-message error";
  el.style.display = "block";
  if (type === "success") {
    setTimeout(() => { el.style.display = "none"; }, 5000);
  }
}

function updateFormAvailability() {
  const submit = document.querySelector("#itinerary-form button[type='submit']");
  const dep = document.getElementById("dep-airport");
  const arr = document.getElementById("arr-airport");
  const msgEl = document.getElementById("form-message");
  if (!submit || !dep || !arr || !msgEl) return;

  const available = window.airportServiceReady && window.itineraryServiceReady;
  submit.disabled = !available;
  dep.disabled = !available;
  arr.disabled = !available;

  if (!available && window.serviceAvailabilityChecked) {
    msgEl.textContent = "El servicio de aeropuertos o itinerarios no está disponible. Activa los servicios y recarga la página.";
    msgEl.className = "form-message error";
    msgEl.style.display = "block";
  } else if (available && msgEl.classList.contains("error")) {
    msgEl.style.display = "none";
  }
}

function applyTheme(theme) {
  document.body.classList.toggle("light-theme", theme === "light");
  document.getElementById("theme-toggle").textContent = theme === "light" ? "Modo Dark" : "Modo Light";
  localStorage.setItem("travelPlannerTheme", theme);
}

function toggleTheme() {
  const current = document.body.classList.contains("light-theme") ? "light" : "dark";
  applyTheme(current === "light" ? "dark" : "light");
}

function loadPreferredTheme() {
  const saved = localStorage.getItem("travelPlannerTheme") || "dark";
  applyTheme(saved);
}


function createAirportMarker(airport) {
  const lat = getAirportLatitude(airport);
  const lon = getAirportLongitude(airport);
  return L.circleMarker([lat, lon], {
    radius: 7,
    color: "#33d6b1",
    fillColor: "#33d6b1",
    fillOpacity: 0.9,
    weight: 2,
  }).bindPopup(
    `<strong>${escapeHtml(getAirportCode(airport))}</strong><br>` +
      `${escapeHtml(getAirportName(airport))}<br>` +
      `${escapeHtml(getAirportCity(airport))}`
  );
}

function createRoute(itinerary, airportById, options = {}) {
  const dep = airportById.get(String(itinerary.departure_airport_id));
  const arr = airportById.get(String(itinerary.arrival_airport_id));
  if (!dep || !arr) return null;

  const depLat = getAirportLatitude(dep);
  const depLon = getAirportLongitude(dep);
  const arrLat = getAirportLatitude(arr);
  const arrLon = getAirportLongitude(arr);
  if (!Number.isFinite(depLat) || !Number.isFinite(depLon) || !Number.isFinite(arrLat) || !Number.isFinite(arrLon)) {
    return null;
  }

  const strokeColor = options.color || "#1e90ff";
  const strokeWeight = options.weight || 6;
  const opacity = options.opacity ?? 0.9;

  const route = L.polyline(
    [
      [depLat, depLon],
      [arrLat, arrLon],
    ],
    {
      color: strokeColor,
      weight: strokeWeight,
      opacity,
      dashArray: options.dashArray || "",
      lineJoin: "round",
      lineCap: "round",
      smoothFactor: 1,
    }
  );

  route.bindPopup(
    `Ruta: ${escapeHtml(getAirportCode(dep))} → ${escapeHtml(getAirportCode(arr))}<br>` +
      `Pasajero: ${escapeHtml(itinerary.user_name)}<br>` +
      `Fecha: ${escapeHtml(itinerary.travel_date)}`
  );
  return route;
}

async function initMapLeaflet() {
  await ensureLeafletLoaded();

  if (window.leafletMap) {
    return;
  }

  window.leafletMap = L.map("airport-map", {
    maxBounds: COLOMBIA_BOUNDS,
    minZoom: 6,
    maxZoom: 10,
    zoomControl: true,
    preferCanvas: true,
  }).setView(COLOMBIA_CENTER, 6);

  window.activeTileLayer = L.tileLayer(OSM_TILE_URL, {
    attribution: TILE_ATTRIBUTION,
    maxZoom: 18,
    minZoom: 1,
  }).addTo(window.leafletMap);

  window.leafletRouteGroup = L.layerGroup().addTo(window.leafletMap);
  window.leafletMarkerGroup = L.layerGroup().addTo(window.leafletMap);

  setTimeout(() => {
    if (window.leafletMap) {
      window.leafletMap.invalidateSize();
    }
  }, 100);
}

function showMapError(message) {
  const mapEl = document.getElementById("airport-map");
  if (!mapEl) return;
  mapEl.innerHTML = "";
  const errorPane = document.createElement("div");
  errorPane.style.cssText = "display:flex;align-items:center;justify-content:center;height:100%;color:#f8f8f8;background:rgba(10,16,32,0.95);padding:24px;text-align:center;font-size:1rem;";
  errorPane.textContent = message;
  mapEl.appendChild(errorPane);
}

async function renderMap() {
  try {
    await initMapLeaflet();
  } catch (err) {
    showMapError(`Error cargando Leaflet: ${escapeHtml(err.message)}`);
    return;
  }

  if (!window.leafletRouteGroup || !window.leafletMarkerGroup) {
    showMapError("Error interno: no se pudo inicializar el mapa.");
    return;
  }

  window.leafletRouteGroup.clearLayers();
  window.leafletMarkerGroup.clearLayers();

  if (!allAirports.length) {
    window.leafletMap.setView(COLOMBIA_CENTER, 6);
    return;
  }

  const airportById = new Map(allAirports.map((airport) => [String(airport.id), airport]));

  allAirports.forEach((airport) => {
    const lat = getAirportLatitude(airport);
    const lon = getAirportLongitude(airport);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
    createAirportMarker(airport).addTo(window.leafletMarkerGroup);
  });

  const routeBounds = [];
  allItineraries.forEach((itinerary) => {
    const route = createRoute(itinerary, airportById, {
      color: "#a8d0ff",
      weight: 4,
      opacity: 0.65,
      dashArray: "8,6",
    });
    if (route) {
      route.addTo(window.leafletRouteGroup);
      routeBounds.push(...route.getLatLngs());
    }
  });

  const selected = getSelectedItinerary();
  if (selected) {
    const highlightRoute = createRoute(selected, airportById, {
      color: "#ff3b30",
      weight: 8,
      opacity: 0.95,
      dashArray: "",
    });
    if (highlightRoute) {
      highlightRoute.addTo(window.leafletRouteGroup);
      routeBounds.push(...highlightRoute.getLatLngs());
    }

    const dep = airportById.get(String(selected.departure_airport_id));
    const arr = airportById.get(String(selected.arrival_airport_id));
    if (dep && arr) {
      const depLat = getAirportLatitude(dep);
      const depLon = getAirportLongitude(dep);
      const arrLat = getAirportLatitude(arr);
      const arrLon = getAirportLongitude(arr);
      if (Number.isFinite(depLat) && Number.isFinite(depLon) && Number.isFinite(arrLat) && Number.isFinite(arrLon)) {
        L.circleMarker([depLat, depLon], {
          radius: 10,
          color: "#00d084",
          fill: true,
          fillColor: "#00d084",
          fillOpacity: 1,
          weight: 2,
        }).addTo(window.leafletMarkerGroup);

        L.circleMarker([arrLat, arrLon], {
          radius: 10,
          color: "#ff3b30",
          fill: true,
          fillColor: "#ff3b30",
          fillOpacity: 1,
          weight: 2,
        }).addTo(window.leafletMarkerGroup);
      }
    }
  }

  let bounds;
  if (routeBounds.length) {
    bounds = L.latLngBounds(routeBounds);
  } else {
    const markerBounds = window.leafletMarkerGroup.getBounds();
    if (markerBounds.isValid()) {
      bounds = markerBounds;
    }
  }

  if (bounds && bounds.isValid()) {
    window.leafletMap.fitBounds(bounds.pad(0.2));
  } else {
    window.leafletMap.setView(COLOMBIA_CENTER, 6);
  }

  window.leafletMap.invalidateSize();
}

function populateAirportSelects(airports) {
  const options = airports
    .map(a => ({
      label: `${a.ciudad || a.city || 'Sin ciudad'} — ${a.nombre || a.name || 'Sin nombre'} (${a.codigo || a.iata_code || a.id})`,
      value: a.id,
      sortKey: (a.ciudad || a.city || '').toString().toLowerCase(),
    }))
    .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
    .map(a => `<option value="${a.value}">${a.label}</option>`)
    .join("");

  const selectHtml = '<option value="">Seleccionar…</option>' + options;
  document.getElementById("dep-airport").innerHTML = selectHtml;
  document.getElementById("arr-airport").innerHTML = selectHtml;
}

function updateAirportCount(count) {
  const el = document.getElementById("airport-count");
  if (el) el.textContent = `${count} aeropuertos`;
}

async function loadItineraries() {
  const listEl = document.getElementById("itinerary-list");
  listEl.innerHTML = '<div class="loader">⏳ Cargando itinerarios…</div>';

  try {
    allItineraries = await fetchItineraries();
    if (!window.selectedItineraryId || !allItineraries.some(it => it.id === window.selectedItineraryId)) {
      window.selectedItineraryId = allItineraries[0]?.id || null;
    }
    renderItineraryList(allItineraries);
    setStatus("itinerary", true);
  } catch (err) {
    listEl.innerHTML = `<div style="color:#ff7a7a;font-size:0.95rem">
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
    renderMap();
    updateSelectedRoutePanel(null);
    return;
  }

  listEl.innerHTML = items.map(it => {
    const dep = getAirportById(it.departure_airport_id);
    const arr = getAirportById(it.arrival_airport_id);
    const routeLabel = dep && arr ? `${getAirportCode(dep)} → ${getAirportCode(arr)}` : `${it.departure_airport_id} → ${it.arrival_airport_id}`;
    const distance = dep && arr ? `${computeGreatCircleDistance(getAirportLatitude(dep), getAirportLongitude(dep), getAirportLatitude(arr), getAirportLongitude(arr)).toFixed(0)} km` : "—";
    return `
      <div class="itinerary-card ${window.selectedItineraryId === it.id ? "selected" : ""}" onclick="selectItinerary(${it.id})" id="card-${it.id}">
        <div class="card-header">
          <div>
            <div class="card-user">👤 ${escapeHtml(it.user_name)}</div>
            <div class="card-date">📅 ${escapeHtml(it.travel_date)}</div>
          </div>
          <div class="card-actions">
            <button class="btn-sm btn-danger" onclick="handleDelete(event, ${it.id})">Eliminar</button>
          </div>
        </div>
        <div class="card-route">✈️ ${escapeHtml(routeLabel)}</div>
        <div class="card-duration">⏱ ${it.duration_minutes} min · ${escapeHtml(distance)}</div>
      </div>
    `;
  }).join("");

  renderMap();
  updateSelectedRoutePanel(getSelectedItinerary());
}

function getSelectedItinerary() {
  return allItineraries.find(it => it.id === window.selectedItineraryId) || null;
}

function selectItinerary(id) {
  window.selectedItineraryId = id;
  renderItineraryList(allItineraries);
  updateSelectedRoutePanel(getSelectedItinerary());
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const msgEl = document.getElementById("form-message");
  msgEl.style.display = "none";

  if (!window.itineraryServiceReady || !window.airportServiceReady) {
    showMessage(msgEl, "No es posible crear el itinerario porque uno de los servicios está offline.", "error");
    return;
  }

  try {
    const depId = document.getElementById("dep-airport").value;
    const arrId = document.getElementById("arr-airport").value;
    const depAirport = getAirportById(depId);
    const arrAirport = getAirportById(arrId);

    if (!depAirport || !arrAirport) {
      throw new Error("Selecciona aeropuertos válidos.");
    }
    if (depId === arrId) {
      throw new Error("El aeropuerto de origen y destino no puede ser igual.");
    }

    const userName = document.getElementById("user-name").value.trim();
    const travelDate = document.getElementById("travel-date").value;

    if (!userName) {
      throw new Error("Ingresa el nombre del pasajero.");
    }
    if (!travelDate) {
      throw new Error("Selecciona la fecha de salida.");
    }

    const durationMinutes = computeDurationMinutes(depAirport, arrAirport);
    if (!Number.isFinite(durationMinutes) || durationMinutes <= 0) {
      throw new Error("No se pudo calcular la duración del vuelo. Verifica los aeropuertos seleccionados.");
    }

    const payload = {
      user_name:            userName,
      departure_airport_id: depId,
      arrival_airport_id:   arrId,
      travel_date:          travelDate,
      duration_minutes:     durationMinutes,
    };

    await createItinerary(payload);
    showMessage(msgEl, `✅ Itinerario creado. Duración estimada ${durationMinutes} min.`, "success");
    e.target.reset();
    await loadItineraries();
  } catch (err) {
    showMessage(msgEl, `❌ ${err.message}`, "error");
  }
}

async function handleDelete(event, id) {
  event.stopPropagation();
  if (!confirm(`¿Eliminar itinerario #${id}?`)) return;

  try {
    await deleteItinerary(id);
    allItineraries = allItineraries.filter(i => i.id !== id);
    if (window.selectedItineraryId === id) {
      window.selectedItineraryId = allItineraries[0]?.id || null;
    }
    renderItineraryList(allItineraries);
    updateSelectedRoutePanel(getSelectedItinerary());
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

function updateSelectedRoutePanel(itinerary) {
  const titleEl = document.getElementById("selected-route-title");
  if (!itinerary) {
    titleEl.textContent = "Ningún vuelo seleccionado";
    document.getElementById("selected-route-route").textContent = "—";
    document.getElementById("selected-route-distance").textContent = "—";
    document.getElementById("selected-route-duration").textContent = "—";
    document.getElementById("selected-route-user").textContent = "—";
    document.getElementById("selected-route-date").textContent = "—";
    return;
  }

  const dep = getAirportById(itinerary.departure_airport_id);
  const arr = getAirportById(itinerary.arrival_airport_id);
  const distanceKm = dep && arr ? computeGreatCircleDistance(getAirportLatitude(dep), getAirportLongitude(dep), getAirportLatitude(arr), getAirportLongitude(arr)).toFixed(0) : "—";

  titleEl.textContent = `${getAirportCode(dep)} → ${getAirportCode(arr)}`;
  document.getElementById("selected-route-route").textContent = dep && arr ? `${airportLabel(dep)} → ${airportLabel(arr)}` : "Datos incompletos";
  document.getElementById("selected-route-distance").textContent = `${distanceKm} km`;
  document.getElementById("selected-route-duration").textContent = `${itinerary.duration_minutes} min`;
  document.getElementById("selected-route-user").textContent = itinerary.user_name;
  document.getElementById("selected-route-date").textContent = itinerary.travel_date;
}

function getMapCenter() {
  const selected = getSelectedItinerary();
  if (selected) {
    const dep = getAirportById(selected.departure_airport_id);
    const arr = getAirportById(selected.arrival_airport_id);
    if (dep && arr) {
      return { lat: (getAirportLatitude(dep) + getAirportLatitude(arr)) / 2, lon: (getAirportLongitude(dep) + getAirportLongitude(arr)) / 2 };
    }
  }

  if (!allAirports.length) return { lat: -15, lon: -60 };
  const avgLat = allAirports.reduce((sum, airport) => sum + getAirportLatitude(airport), 0) / allAirports.length;
  const avgLon = allAirports.reduce((sum, airport) => sum + getAirportLongitude(airport), 0) / allAirports.length;
  return { lat: avgLat, lon: avgLon };
}

async function fetchWithTimeout(resource, options = {}) {
  const { timeout = 3000, ...rest } = options;
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(resource, { signal: controller.signal, ...rest });
  } finally {
    clearTimeout(id);
  }
}

async function checkServices() {
  for (const [svc, url] of [["airport", CONFIG.AIRPORT_SERVICE], ["itinerary", CONFIG.ITINERARY_SERVICE]]) {
    try {
      const r = await fetchWithTimeout(`${url}/health`, { timeout: 3000 });
      setStatus(svc, r.ok);
    } catch {
      setStatus(svc, false);
    }
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  loadPreferredTheme();
  updateFormAvailability();
  const today = new Date().toISOString().split("T")[0];
  document.getElementById("travel-date").min = today;
  document.getElementById("itinerary-form").addEventListener("submit", handleFormSubmit);

  try {
    allAirports = await fetchAirports();
    populateAirportSelects(allAirports);
    updateAirportCount(allAirports.length);
    setStatus("airport", true);
  } catch (err) {
    document.getElementById("airport-count").textContent = "0 aeropuertos";
    setStatus("airport", false);
  }

  await loadItineraries();
  await checkServices();

  try {
    await renderMap();
  } catch (err) {
    showMapError(`Error de renderizado: ${escapeHtml(err.message)}`);
    console.error("Render map error:", err);
  }
});
