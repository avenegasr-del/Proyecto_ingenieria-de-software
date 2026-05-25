# ✈️ Travel Planner — Sistema de Itinerarios de Viaje

Sistema de planificación de viajes construido con **microservicios**, **arquitectura hexagonal** y el **patrón Adapter**.

---

## 🚀 Inicio Rápido (1 comando)

```bash
# Con Docker (recomendado):
python run.py docker

# O menú interactivo:
python run.py
```

---

## 📁 Estructura del Proyecto

```
travel-planner/
├── run.py                          ← CLASE MAESTRA — ejecuta todo
├── docker-compose.yml
├── airport-service/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── entities/airport.py          # Entidad pura
│   │   │   └── ports/airport_external_port.py  # Puerto abstracto
│   │   ├── application/
│   │   │   └── services/airport_query_service.py
│   │   ├── infrastructure/
│   │   │   └── adapters/
│   │   │       ├── api_colombia_adapter.py   # ← PATRÓN ADAPTER
│   │   │       └── api_colombia_dto.py
│   │   ├── api/
│   │   │   ├── routers/airports_router.py
│   │   │   ├── schemas.py
│   │   │   └── dependencies.py
│   │   └── main.py
│   └── tests/
├── itinerary-service/
│   ├── app/
│   │   ├── domain/
│   │   │   ├── entities/itinerary.py
│   │   │   └── ports/
│   │   │       ├── itinerary_repository_port.py
│   │   │       └── airport_validation_port.py
│   │   ├── application/
│   │   │   └── services/
│   │   │       ├── itinerary_command_service.py
│   │   │       └── itinerary_query_service.py
│   │   ├── infrastructure/
│   │   │   ├── adapters/airport_http_adapter.py
│   │   │   ├── database/models.py + session.py
│   │   │   └── repositories/sqlalchemy_itinerary_repository.py
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/map.js
└── load-tests/locustfile.py
```

---

## 🐳 Docker

```bash
# Levantar todo:
docker compose up --build

# Con SonarQube:
docker compose --profile sonar up --build

# Ver logs:
docker compose logs -f

# Detener:
docker compose down
```

---

## 🐍 Local (sin Docker)

```bash
# 1. Instalar dependencias:
python run.py install

# 2. Iniciar servicios:
python run.py local
```

---

## 🌐 URLs

| Servicio           | URL                             |
|--------------------|---------------------------------|
| Frontend           | http://localhost:3000           |
| Airport Swagger    | http://localhost:8001/docs      |
| Itinerary Swagger  | http://localhost:8002/docs      |
| Airport Health     | http://localhost:8001/health    |
| Itinerary Health   | http://localhost:8002/health    |

---

## 📡 Endpoints

### Airport Service (:8001)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/airports` | Lista todos los aeropuertos |
| GET | `/airports/{id}` | Obtiene aeropuerto por ID |
| GET | `/airports/plotly` | Datos para Plotly JS |
| GET | `/health` | Health check |

### Itinerary Service (:8002)
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/itineraries` | Crear itinerario |
| GET | `/itineraries` | Listar itinerarios |
| GET | `/itineraries/{id}` | Obtener itinerario |
| PUT | `/itineraries/{id}` | Actualizar itinerario |
| DELETE | `/itineraries/{id}` | Eliminar itinerario |
| GET | `/health` | Health check |

---

## 🧪 Pruebas

```bash
# Todas las pruebas:
python run.py test

# Pruebas individuales:
cd airport-service && pytest tests/ -v
cd itinerary-service && pytest tests/ -v

# Con cobertura:
pytest tests/ -v --cov=app --cov-report=html
```

---

## 🏋️ Pruebas de Carga

```bash
pip install locust
locust -f load-tests/locustfile.py
# Abrir: http://localhost:8089
```

---

## 🔷 Patrón Adapter

El `ApiColombiaAdapter` implementa `IAirportExternalPort`:

```
IAirportExternalPort (Puerto abstracto — Domain layer)
         ↑
         | implements
ApiColombiaAdapter (Adaptador concreto — Infrastructure layer)
         |
         → httpx.Client → API Colombia (externa)
```

El dominio y los casos de uso **nunca** conocen API Colombia.
Solo interactúan con el puerto abstracto.

---

## 🛠️ Comandos `run.py`

```bash
python run.py              # Menú interactivo
python run.py docker       # Docker Compose
python run.py local        # Local sin Docker
python run.py test         # Pytest
python run.py install      # Instalar dependencias
python run.py status       # Estado de servicios
python run.py stop         # Detener todo
python run.py urls         # Mostrar URLs
```
