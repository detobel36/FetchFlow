import ipaddress
import socket
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Query, Response
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
    filepath: str | None = None


class SaveConfigRequest(BaseModel):
    """Schema for saving configuration request body."""

    config_json: str
    filepath: str | None = None


class ExportConfigRequest(BaseModel):
    """Schema for exporting configuration request body."""

    config_json: str
    filename: str | None = None


@app.post("/api/config/validate")
def validate_config(req: ConfigRequest) -> dict[str, Any]:
    """Validate JSON configuration."""
    return validate_scraper_json(req.config_json)


@app.post("/api/config/save")
def save_config(req: SaveConfigRequest) -> dict[str, Any]:
    """Save JSON configuration to file path on disk."""
    try:
        return session.save_config(req.config_json, filepath=req.filepath)
    except Exception as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


@app.post("/api/config/export")
def export_config(req: ExportConfigRequest) -> Response:
    """Export and download JSON configuration as attachment file."""
    val = validate_scraper_json(req.config_json)
    if not val["valid"]:
        raise HTTPException(status_code=400, detail="Cannot export invalid JSON configuration.")

    filename = req.filename
    if not filename:
        cfg_name = val.get("config", {}).get("name") if val.get("config") else None
        filename = f"{cfg_name}.json" if cfg_name else "scraper_config.json"

    if not filename.endswith(".json"):
        filename += ".json"

    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=req.config_json, media_type="application/json", headers=headers)


@app.post("/api/session/load")
def load_session(req: ConfigRequest) -> dict[str, Any]:
    """Load and start debug session with configuration string."""
    session.load_config(req.config_json, config_path=req.filepath)
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


def is_forbidden_ip(ip_str: str) -> bool:
    """Check if IP address is private, loopback, link-local, multicast, reserved, or unspecified."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False
    else:
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )


def validate_proxy_url(url: str) -> None:
    """Validate proxy target URL to prevent Server-Side Request Forgery (SSRF)."""
    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL scheme. Must start with http:// or https://")

    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="Invalid URL: Missing hostname.")

    hostname_lower = hostname.lower()
    forbidden_msg = "Access to private or local network resources is forbidden via proxy."
    if hostname_lower == "localhost" or hostname_lower.endswith(".localhost"):
        raise HTTPException(status_code=400, detail=forbidden_msg)

    if is_forbidden_ip(hostname_lower):
        raise HTTPException(status_code=400, detail=forbidden_msg)

    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for _, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            if is_forbidden_ip(ip_str):
                raise HTTPException(status_code=400, detail=forbidden_msg)
    except socket.gaierror as err:
        raise HTTPException(status_code=400, detail=f"Failed to resolve hostname '{hostname}': {err}") from err


@app.get("/api/proxy")
async def proxy_url(
    url: Annotated[str, Query(description="Target URL to fetch via proxy")],
) -> Response:
    """Proxy HTTP GET request to bypass CORS restrictions for preview."""
    validate_proxy_url(url)

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url)
            headers_to_exclude = {
                "content-encoding",
                "content-length",
                "transfer-encoding",
                "content-security-policy",
                "x-frame-options",
            }
            response_headers = {
                k: v for k, v in resp.headers.items() if k.lower() not in headers_to_exclude
            }
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=response_headers,
                media_type=resp.headers.get("content-type"),
            )
    except httpx.RequestError as err:
        raise HTTPException(status_code=502, detail=f"Proxy error fetching target URL: {err}") from err


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
