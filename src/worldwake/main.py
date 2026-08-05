"""Application entry point for the WorldWake web service.

This module wires the FastAPI app, registers the API routes, and serves the
frontend assets that power the WorldSeed experience.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from worldwake.world_seed import router as world_seed_router

from worldwake.api_errors import install_error_handlers


from worldwake.auth.router import (
    router as auth_router,
)


# Resolve the package and static asset directories from this module location.
PACKAGE_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = PACKAGE_DIRECTORY / "static"


# Create the FastAPI application with basic metadata for the WorldWake experience.
app = FastAPI(
    title="WorldWake",
    description="Create a world, record its history, and keep it moving.",
    version="0.1.0",
)

install_error_handlers(app)

# Register the API endpoints that manage world seeds and generation requests.
app.include_router(auth_router)
app.include_router(world_seed_router)


# Serve frontend assets from the static folder so the UI can load correctly.
app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIRECTORY)),
    name="static",
)


@app.get("/", include_in_schema=False)
async def show_home_page() -> FileResponse:
    """Return the main WorldSeed landing page."""

    return FileResponse(STATIC_DIRECTORY / "index.html")
