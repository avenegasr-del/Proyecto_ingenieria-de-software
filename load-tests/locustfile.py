"""
Load tests for Travel Planner microservices.
Run: locust -f locustfile.py
"""
import random
from datetime import date, timedelta
from locust import HttpUser, task, between, events


AIRPORTS = ["1", "2", "3", "4", "5", "6", "7", "8"]


def future_date(days_ahead: int = None) -> str:
    days = days_ahead or random.randint(1, 60)
    return (date.today() + timedelta(days=days)).isoformat()


# ── Airport Service Users ──────────────────────────────────────────────────────
class AirportServiceUser(HttpUser):
    """Simulates users browsing airport data."""
    host = "http://localhost:8001"
    wait_time = between(1, 3)

    @task(4)
    def list_airports(self):
        self.client.get("/airports", name="GET /airports")

    @task(3)
    def get_plotly_data(self):
        self.client.get("/airports/plotly", name="GET /airports/plotly")

    @task(2)
    def get_airport_by_id(self):
        airport_id = random.choice(AIRPORTS)
        self.client.get(f"/airports/{airport_id}", name="GET /airports/{id}")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="GET /health (airport)")


# ── Itinerary Service Users ────────────────────────────────────────────────────
class ItineraryServiceUser(HttpUser):
    """Simulates users creating and managing itineraries."""
    host = "http://localhost:8002"
    wait_time = between(2, 5)

    def on_start(self):
        """Create initial itinerary to have data for GET tests."""
        self._create_itinerary()

    def _create_itinerary(self) -> int | None:
        dep, arr = random.sample(AIRPORTS, 2)
        payload = {
            "user_name": f"LoadUser_{random.randint(1, 1000)}",
            "departure_airport_id": dep,
            "arrival_airport_id": arr,
            "travel_date": future_date(),
            "duration_minutes": random.randint(30, 360),
        }
        with self.client.post("/itineraries", json=payload,
                              name="POST /itineraries", catch_response=True) as r:
            if r.status_code == 201:
                return r.json().get("id")
            r.failure(f"Create failed: {r.status_code}")
        return None

    @task(3)
    def list_itineraries(self):
        self.client.get("/itineraries", name="GET /itineraries")

    @task(2)
    def create_itinerary(self):
        self._create_itinerary()

    @task(1)
    def get_itinerary(self):
        self.client.get("/itineraries/1", name="GET /itineraries/{id}")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="GET /health (itinerary)")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("\n🚀 Load test starting — Travel Planner Microservices")
    print(f"   Airport Service:   http://localhost:8001")
    print(f"   Itinerary Service: http://localhost:8002\n")
