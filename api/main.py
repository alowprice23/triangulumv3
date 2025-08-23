import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import threading
from prometheus_client import make_asgi_app, REGISTRY
from starlette.routing import Mount

from runtime.supervisor import Supervisor

logger = logging.getLogger(__name__)

# --- Data Models ---
class BugSubmission(BaseModel):
    description: str
    severity: int = 5

class StatusResponse(BaseModel):
    is_running: bool
    queued_tickets: int
    active_sessions: int

# --- Shared State ---
# This dictionary will hold our single supervisor instance
# In a real production app, you might use a more robust solution like a
# dedicated service manager or a dependency injection framework.
shared_state = {}

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages the lifecycle of the Supervisor.
    It starts the Supervisor in a background thread when the API starts
    and stops it when the API shuts down.
    """
    logger.info("API Lifespan: Startup")
    # Assume the repository to be fixed is in the current working directory
    repo_root = Path.cwd() / "buggy_project"
    supervisor = Supervisor(repo_root=repo_root)
    shared_state["supervisor"] = supervisor

    # Run the supervisor's main loop in a background thread
    # We'll let it run indefinitely (or until shutdown) by passing a large duration
    supervisor_thread = threading.Thread(
        target=supervisor.run,
        args=(3600*24,), # Run for 24 hours, effectively "forever"
        daemon=True
    )
    supervisor_thread.start()

    yield # The API is now running

    logger.info("API Lifespan: Shutdown")
    supervisor.stop() # Signal the supervisor to stop
    # The thread is a daemon, so it will be terminated on exit

# --- Metrics App ---
metrics_app = make_asgi_app()

# --- FastAPI App ---
# We mount the metrics app on a sub-route.
routes = [
    Mount("/metrics", app=metrics_app)
]

app = FastAPI(lifespan=lifespan, routes=routes)


# --- API Endpoints ---
@app.post("/bugs", status_code=202)
def submit_bug(bug: BugSubmission):
    """
    Submits a new bug to the supervisor.
    """
    supervisor = shared_state.get("supervisor")
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not running.")

    supervisor.submit_bug(bug.description, bug.severity)
    return {"message": "Bug ticket submitted successfully."}

@app.get("/status", response_model=StatusResponse)
def get_status():
    """
    Gets the current status of the supervisor.
    """
    supervisor = shared_state.get("supervisor")
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not running.")

    return StatusResponse(
        is_running=supervisor.is_running,
        queued_tickets=len(supervisor.scheduler),
        active_sessions=supervisor.executor.get_active_session_count()
    )

@app.get("/")
def read_root():
    return {"message": "Triangulum Agentic Bug-Fixing System API"}
