from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from worldwake.world_seed import router as world_seed_router


# Resolve the package and static asset directories from this module location.
PACKAGE_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = PACKAGE_DIRECTORY / "static"


# Create the FastAPI application with basic metadata for the WorldWake experience.
app = FastAPI(
    title="WorldWake",
    description="Create a world, record its history, and keep it moving.",
    version="0.1.0",
)

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
