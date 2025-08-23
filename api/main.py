import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import threading
from prometheus_client import make_asgi_app, REGISTRY
from starlette.routing import Mount
import uuid

from runtime.supervisor import Supervisor
from discovery.code_graph import CodeGraph, CodeGraphBuilder

logger = logging.getLogger(__name__)

# --- Data Models ---
class AnalysisRequest(BaseModel):
    repo_path: str

class AnalysisResponse(BaseModel):
    session_id: str

class BugSubmission(BaseModel):
    description: str
    severity: int = 5
    session_id: str | None = None

class StatusResponse(BaseModel):
    is_running: bool
    queued_tickets: int
    active_sessions: int

# --- Shared State ---
# This dictionary will hold our single supervisor instance and the cache for code graphs.
# In a real production app, you might use a more robust solution like Redis
# for caching, especially if the API runs in a multi-worker setup.
shared_state: Dict[str, Any] = {
    "supervisor": None,
    "code_graph_cache": {}
}

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

@app.post("/analysis-sessions", response_model=AnalysisResponse)
def create_analysis_session(request: AnalysisRequest):
    """
    Creates a new analysis session by building and caching a CodeGraph for a given repository path.
    """
    session_id = str(uuid.uuid4())
    repo_path = Path(request.repo_path)

    if not repo_path.is_dir():
        raise HTTPException(status_code=404, detail=f"Repository path not found: {repo_path}")

    logger.info(f"Starting CodeGraph build for session {session_id} at path {repo_path}")
    try:
        builder = CodeGraphBuilder(repo_root=repo_path)
        code_graph = builder.build()

        # Cache the built graph
        shared_state["code_graph_cache"][session_id] = code_graph
        logger.info(f"CodeGraph for session {session_id} built and cached successfully.")

        return AnalysisResponse(session_id=session_id)
    except Exception as e:
        logger.error(f"Failed to build CodeGraph for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze the repository.")


@app.post("/bugs", status_code=202)
def submit_bug(bug: BugSubmission):
    """
    Submits a new bug to the supervisor.
    """
    supervisor = shared_state.get("supervisor")
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not running.")

    code_graph = None
    if bug.session_id:
        code_graph = shared_state["code_graph_cache"].get(bug.session_id)
        if code_graph is None:
            raise HTTPException(status_code=404, detail=f"Analysis session {bug.session_id} not found or expired.")

    supervisor.submit_bug(bug.description, bug.severity, code_graph=code_graph)
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
