#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          TRAVEL PLANNER — CLASE MAESTRA DE EJECUCIÓN                        ║
║          Microservicios | Arquitectura Hexagonal | Patrón Adapter            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  USO:                                                                        ║
║    python run.py                      → menú interactivo                    ║
║    python run.py docker               → levantar con Docker Compose          ║
║    python run.py local                → levantar en local (sin Docker)       ║
║    python run.py test                 → ejecutar todas las pruebas            ║
║    python run.py stop                 → detener todos los servicios           ║
║    python run.py status               → verificar estado de servicios         ║
║    python run.py install              → instalar dependencias locales         ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import signal
import subprocess
import threading
import platform
import webbrowser
from pathlib import Path
from typing import Optional


# ── Configuration ──────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
AIRPORT_DIR     = BASE_DIR / "airport-service"
ITINERARY_DIR   = BASE_DIR / "itinerary-service"
FRONTEND_DIR    = BASE_DIR / "frontend"
LOAD_TESTS_DIR  = BASE_DIR / "load-tests"

AIRPORT_PORT    = 8001
ITINERARY_PORT  = 8002
FRONTEND_PORT   = 3000

AIRPORT_URL     = f"http://127.0.0.1:{AIRPORT_PORT}"
ITINERARY_URL   = f"http://127.0.0.1:{ITINERARY_PORT}"
FRONTEND_URL    = f"http://127.0.0.1:{FRONTEND_PORT}"

IS_WINDOWS      = platform.system() == "Windows"
PYTHON          = sys.executable

# ── Colors ─────────────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GREY   = "\033[90m"

def _c(color: str, text: str) -> str:
    if IS_WINDOWS:
        return text
    return f"{color}{text}{C.RESET}"

def ok(msg):    print(_c(C.GREEN,  f"  ✅  {msg}"))
def err(msg):   print(_c(C.RED,    f"  ❌  {msg}"))
def info(msg):  print(_c(C.CYAN,   f"  ℹ️   {msg}"))
def warn(msg):  print(_c(C.YELLOW, f"  ⚠️   {msg}"))
def step(msg):  print(_c(C.BLUE,   f"\n  ▶   {msg}"))
def title(msg): print(_c(C.BOLD + C.WHITE, f"\n{'═'*60}\n  {msg}\n{'═'*60}"))

# ── Running processes (local mode) ─────────────────────────────────────────────
_processes: list[subprocess.Popen] = []
_http_server: Optional[subprocess.Popen] = None


# ── Utilities ──────────────────────────────────────────────────────────────────
def run(cmd: list[str], cwd: Path = BASE_DIR, check: bool = True,
        capture: bool = False) -> subprocess.CompletedProcess:
    kwargs = dict(cwd=str(cwd), capture_output=capture, text=capture)
    if check:
        return subprocess.run(cmd, check=True, **kwargs)
    return subprocess.run(cmd, **kwargs)


def check_command(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def wait_for_service(url: str, name: str, timeout: int = 60) -> bool:
    """Polls a /health endpoint until it responds or timeout."""
    import urllib.request, urllib.error
    step(f"Waiting for {name} to be ready…")
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=3) as r:
                if r.status == 200:
                    ok(f"{name} is ready at {url}")
                    return True
        except Exception:
            pass
        time.sleep(2)
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    err(f"{name} did not start within {timeout}s")
    return False


def wait_for_port(port: int, name: str, timeout: int = 30) -> bool:
    """Waits until the service binds to a TCP port."""
    step(f"Waiting for {name} port {port} to bind…")
    start = time.time()
    while time.time() - start < timeout:
        if port_in_use(port):
            ok(f"{name} port {port} is bound")
            return True
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
    print()
    err(f"{name} port {port} did not bind within {timeout}s")
    return False


def open_browser_tabs():
    time.sleep(2)
    for label, url in [
        ("Frontend",         FRONTEND_URL),
        ("Airport Swagger",  f"{AIRPORT_URL}/docs"),
        ("Itinerary Swagger",f"{ITINERARY_URL}/docs"),
    ]:
        info(f"Opening {label}: {url}")
        webbrowser.open(url)
        time.sleep(0.5)


# ── Install ────────────────────────────────────────────────────────────────────
def cmd_install():
    title("INSTALLING DEPENDENCIES")
    for service, d in [("airport-service", AIRPORT_DIR), ("itinerary-service", ITINERARY_DIR)]:
        step(f"Installing {service}")
        req = d / "requirements.txt"
        if not req.exists():
            err(f"requirements.txt not found in {d}")
            continue
        run([PYTHON, "-m", "pip", "install", "-r", str(req), "-q"])
        ok(f"{service} dependencies installed")
    ok("All dependencies installed")


# ── Test ───────────────────────────────────────────────────────────────────────
def cmd_test(service: str = "all"):
    title("RUNNING TESTS")
    results = {}

    services = {
        "airport":   (AIRPORT_DIR,   "Airport Service"),
        "itinerary": (ITINERARY_DIR, "Itinerary Service"),
    }

    to_run = services if service == "all" else {service: services[service]}

    for key, (d, name) in to_run.items():
        step(f"Running tests for {name}")
        env = {**os.environ, "PYTHONPATH": str(d)}
        result = subprocess.run(
            [PYTHON, "-m", "pytest", "tests/", "-v", "--tb=short"],
            cwd=str(d), env=env
        )
        results[name] = result.returncode == 0

    print()
    title("TEST RESULTS")
    all_ok = True
    for name, passed in results.items():
        if passed: ok(f"{name}: PASSED")
        else:      err(f"{name}: FAILED"); all_ok = False

    if all_ok: ok("All tests passed ✅")
    return all_ok


# ── Status ─────────────────────────────────────────────────────────────────────
def cmd_status():
    import urllib.request
    title("SERVICE STATUS")
    services = [
        ("Airport Service",   AIRPORT_URL,   AIRPORT_PORT),
        ("Itinerary Service", ITINERARY_URL, ITINERARY_PORT),
        ("Frontend",          FRONTEND_URL,  FRONTEND_PORT),
    ]
    for name, url, port in services:
        if not port_in_use(port):
            print(f"  {'🔴'} {name:<22} port {port} — not running")
            continue
        try:
            if "Frontend" in name:
                with urllib.request.urlopen(url, timeout=3): pass
                print(f"  {'🟢'} {name:<22} {url}")
            else:
                with urllib.request.urlopen(f"{url}/health", timeout=3) as r:
                    status = "healthy" if r.status == 200 else "degraded"
                    print(f"  {'🟢'} {name:<22} {url}/docs  [{status}]")
        except Exception as e:
            print(f"  🟡 {name:<22} port {port} open but health check failed: {e}")


# ── Stop ───────────────────────────────────────────────────────────────────────
def cmd_stop():
    title("STOPPING SERVICES")
    # Stop local processes
    for p in _processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            pass
    _processes.clear()

    # Stop Docker
    if check_command("docker"):
        compose_file = BASE_DIR / "docker-compose.yml"
        if compose_file.exists():
            step("Stopping Docker Compose services…")
            subprocess.run(
                ["docker", "compose", "-f", str(compose_file), "down"],
                capture_output=True
            )
            ok("Docker services stopped")

    # Kill processes on ports
    for port in [AIRPORT_PORT, ITINERARY_PORT, FRONTEND_PORT]:
        kill_port(port)
    ok("All services stopped")


def kill_port(port: int):
    if IS_WINDOWS:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{port} " in line and "LISTENING" in line:
                parts = [p for p in line.split() if p]
                if parts:
                    pid = parts[-1]
                    subprocess.run(["taskkill", "/PID", pid, "/F"], capture_output=True, text=True)
    else:
        subprocess.run(f"lsof -ti:{port} | xargs kill -9 2>/dev/null || true",
                       shell=True, capture_output=True)


# ── Docker Mode ────────────────────────────────────────────────────────────────
def cmd_docker(open_tabs: bool = True):
    title("STARTING WITH DOCKER COMPOSE")

    if not check_command("docker"):
        err("Docker is not installed. Install from https://docker.com")
        sys.exit(1)

    compose_file = BASE_DIR / "docker-compose.yml"
    if not compose_file.exists():
        err(f"docker-compose.yml not found at {compose_file}")
        sys.exit(1)

    # Check if already running
    for port, name in [(AIRPORT_PORT, "Airport"), (ITINERARY_PORT, "Itinerary")]:
        if port_in_use(port):
            warn(f"Port {port} ({name} Service) already in use")

    step("Building and starting all services…")
    info("This may take a few minutes on first run (downloading images + building)")
    print()

    try:
        run(["docker", "compose", "-f", str(compose_file), "up", "--build", "-d"])
    except subprocess.CalledProcessError:
        err("docker compose up failed. Check Docker is running.")
        sys.exit(1)

    # Wait for services
    wait_for_service(AIRPORT_URL,   "Airport Service",   timeout=90)
    wait_for_service(ITINERARY_URL, "Itinerary Service", timeout=90)

    _print_urls()

    if open_tabs:
        info("Opening browser tabs in 3 seconds…")
        threading.Thread(target=open_browser_tabs, daemon=True).start()

    print()
    ok("System running via Docker! Press Ctrl+C to stop.")
    print(_c(C.GREY, f"\n  Logs: docker compose logs -f\n  Stop: docker compose down\n"))

    try:
        while True:
            time.sleep(10)
            cmd_status()
    except KeyboardInterrupt:
        print()
        step("Shutting down…")
        run(["docker", "compose", "-f", str(compose_file), "down"])
        ok("All services stopped.")


# ── Local Mode ─────────────────────────────────────────────────────────────────
def cmd_local(open_tabs: bool = True):
    title("STARTING IN LOCAL MODE (without Docker)")

    # Check ports free
    for port, name in [(AIRPORT_PORT, "Airport"), (ITINERARY_PORT, "Itinerary"), (FRONTEND_PORT, "Frontend")]:
        if port_in_use(port):
            warn(f"Port {port} is already in use. Attempting to free it…")
            kill_port(port)
            time.sleep(1)

    env_airport = {
        **os.environ,
        "PYTHONPATH": str(AIRPORT_DIR),
        "API_COLOMBIA_URL": "https://api-colombia.com/api/v1",
        "LOG_LEVEL": "INFO",
    }
    env_itinerary = {
        **os.environ,
        "PYTHONPATH": str(ITINERARY_DIR),
        "DATABASE_URL": f"sqlite:///{ITINERARY_DIR}/itineraries.db",
        "AIRPORT_SERVICE_URL": f"http://127.0.0.1:{AIRPORT_PORT}",
        "LOG_LEVEL": "INFO",
    }

    # Start Airport Service
    step("Starting Airport Service…")
    p1 = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(AIRPORT_PORT), "--reload"],
        cwd=str(AIRPORT_DIR), env=env_airport,
    )
    _processes.append(p1)

    # Wait for Airport Service before starting Itinerary
    if not wait_for_service(AIRPORT_URL, "Airport Service", timeout=30):
        err("Airport Service failed to start. Check requirements are installed.")
        err("Run: python run.py install")
        cmd_stop()
        sys.exit(1)

    # Start Itinerary Service
    step("Starting Itinerary Service…")
    p2 = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(ITINERARY_PORT), "--reload"],
        cwd=str(ITINERARY_DIR), env=env_itinerary,
    )
    _processes.append(p2)
    if not wait_for_port(ITINERARY_PORT, "Itinerary Service", timeout=30):
        if p2.poll() is not None:
            err(f"Itinerary Service exited unexpectedly (code {p2.returncode})")
        else:
            err("Itinerary Service port did not bind within 30 seconds.")
        err("Run: python run.py install")
        cmd_stop()
        sys.exit(1)

    if not wait_for_service(ITINERARY_URL, "Itinerary Service", timeout=30):
        warn("Itinerary Service port is bound, but health endpoint did not respond quickly.")
        warn("Continuing startup; the service may become healthy shortly.")

    # Start Frontend with Python HTTP server
    step("Starting Frontend (Python HTTP server)…")
    p3 = subprocess.Popen(
        [PYTHON, "-m", "http.server", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
    )
    _processes.append(p3)
    time.sleep(2)
    ok(f"Frontend available at {FRONTEND_URL}")

    _print_urls()

    if open_tabs:
        threading.Thread(target=open_browser_tabs, daemon=True).start()

    def on_signal(sig, frame):
        print()
        step("Shutting down local services…")
        cmd_stop()
        ok("All services stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT,  on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    ok("System running locally! Press Ctrl+C to stop.")
    print()
    try:
        while True:
            time.sleep(1)
            # Check if any process died
            for i, p in enumerate(_processes):
                if p.poll() is not None:
                    warn(f"Process {i} exited unexpectedly (code {p.returncode})")
    except KeyboardInterrupt:
        on_signal(None, None)


# ── Helpers ────────────────────────────────────────────────────────────────────
def _print_urls():
    print()
    print(_c(C.BOLD, "  URLS DEL SISTEMA:"))
    print(_c(C.GREEN,  f"    🌐 Frontend:          {FRONTEND_URL}"))
    print(_c(C.CYAN,   f"    ✈️  Airport Swagger:   {AIRPORT_URL}/docs"))
    print(_c(C.CYAN,   f"    📋 Itinerary Swagger:  {ITINERARY_URL}/docs"))
    print(_c(C.GREY,   f"    🔍 Airport Health:     {AIRPORT_URL}/health"))
    print(_c(C.GREY,   f"    🔍 Itinerary Health:   {ITINERARY_URL}/health"))


def _print_menu():
    print(_c(C.BOLD + C.WHITE, """
╔══════════════════════════════════════════════════════════════╗
║       ✈️  TRAVEL PLANNER — SISTEMA DE MICROSERVICIOS         ║
║          Arquitectura Hexagonal + Patrón Adapter             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   1) 🐳 Iniciar con Docker  (RECOMENDADO)                    ║
║   2) 🐍 Iniciar en local    (sin Docker)                     ║
║   3) 🧪 Ejecutar pruebas    (Pytest)                         ║
║   4) 📦 Instalar dependencias locales                        ║
║   5) 📊 Ver estado de servicios                              ║
║   6) ⛔ Detener todos los servicios                           ║
║   7) 🔗 Mostrar URLs del sistema                             ║
║   8) 🚪 Salir                                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""))


def _validate_project_structure():
    required = [
        AIRPORT_DIR / "app" / "main.py",
        AIRPORT_DIR / "requirements.txt",
        AIRPORT_DIR / "Dockerfile",
        ITINERARY_DIR / "app" / "main.py",
        ITINERARY_DIR / "requirements.txt",
        ITINERARY_DIR / "Dockerfile",
        FRONTEND_DIR / "index.html",
        BASE_DIR / "docker-compose.yml",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        err("Missing required files:")
        for m in missing: print(f"     - {m}")
        sys.exit(1)


# ── Entry Point ────────────────────────────────────────────────────────────────
def main():
    _validate_project_structure()

    args = sys.argv[1:]
    cmd = args[0].lower() if args else "menu"

    if args:
        if cmd == "docker":        cmd_docker(); return
        elif cmd == "local":       cmd_local(); return
        elif cmd == "test":        cmd_test(); return
        elif cmd == "stop":        cmd_stop(); return
        elif cmd == "status":      cmd_status(); return
        elif cmd == "install":     cmd_install(); return
        elif cmd == "urls":        _print_urls(); return
        elif cmd in ("menu", "interactive"):
            pass
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python run.py [docker|local|test|stop|status|install|menu]")
            sys.exit(1)

    if cmd in ("menu", "interactive"):
        # Interactive menu
        while True:
            _print_menu()
            try:
                choice = input(_c(C.CYAN, "  Selecciona una opción (1-8): ")).strip()
            except (KeyboardInterrupt, EOFError):
                print()
                ok("¡Hasta luego! ✈️")
                sys.exit(0)

            if choice == "1":
                cmd_docker()
            elif choice == "2":
                cmd_local()
            elif choice == "3":
                cmd_test()
            elif choice == "4":
                cmd_install()
            elif choice == "5":
                cmd_status()
            elif choice == "6":
                cmd_stop()
            elif choice == "7":
                _print_urls()
            elif choice == "8":
                ok("¡Hasta luego! ✈️")
                sys.exit(0)
            else:
                warn("Opción inválida. Elige entre 1 y 8.")


if __name__ == "__main__":
    main()
