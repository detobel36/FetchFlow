from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from preview.session import DebugSession
from preview.validation import validate_scraper_json

app = FastAPI(title="Scraper Preview & Debugger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = DebugSession()


class ConfigRequest(BaseModel):
    """Schema for config request body."""

    config_json: str


@app.post("/api/config/validate")
def validate_config(req: ConfigRequest) -> dict[str, Any]:
    """Validate JSON configuration."""
    return validate_scraper_json(req.config_json)


@app.post("/api/session/load")
def load_session(req: ConfigRequest) -> dict[str, Any]:
    """Load and start debug session with configuration string."""
    session.load_config(req.config_json)
    return session.start()


@app.post("/api/session/start")
def start_session() -> dict[str, Any]:
    """Start or restart debug session."""
    try:
        return session.start()
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


@app.post("/api/session/next")
def next_step() -> dict[str, Any]:
    """Advance to next step/iteration."""
    return session.next()


@app.post("/api/session/previous")
def previous_step() -> dict[str, Any]:
    """Navigate backward to previous step/iteration."""
    return session.previous()


@app.post("/api/session/next-iteration")
def next_iteration() -> dict[str, Any]:
    """Navigate to next iteration in loop."""
    return session.next_iteration()


@app.post("/api/session/previous-iteration")
def previous_iteration() -> dict[str, Any]:
    """Navigate to previous iteration in loop."""
    return session.previous_iteration()


@app.post("/api/session/rerun")
def rerun_current_step(req: ConfigRequest | None = None) -> dict[str, Any]:
    """Re-run active step with current JSON configuration."""
    if req and req.config_json:
        session.raw_json = req.config_json
    return session.rerun_current_step()


@app.post("/api/session/restart")
def restart_session() -> dict[str, Any]:
    """Reset debug session and start over from first step."""
    return session.restart()


@app.get("/api/session/state")
def get_session_state() -> dict[str, Any]:
    """Get active session state."""
    return session.get_state()


@app.get("/api/preview-html")
def get_preview_html() -> Response:
    """Return highlighted HTML string for iframe rendering."""
    state = session.get_state()
    fallback = "<html><body><p>No HTML preview available.</p></body></html>"
    html = state.get("highlighted_html") or state.get("raw_html") or fallback
    return Response(content=html, media_type="text/html")


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
