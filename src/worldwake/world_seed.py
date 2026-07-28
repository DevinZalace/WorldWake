"""HTTP API for uploading world seeds and requesting fantasy maps.

The router stores uploaded images and generation requests on disk so the rest
of the application can work with simple JSON metadata files while the full
world-generation engine is still being developed.
"""

from __future__ import annotations

import json
import os
import secrets
from datetime import UTC, datetime
from enum import StrEnum
from io import BytesIO
from pathlib import Path
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api", tags=["WorldSeed"])

# Guard the upload flow against oversized payloads and unsupported media.
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
SUPPORTED_IMAGE_FORMATS = {
    "GIF": (".gif", "image/gif"),
    "JPEG": (".jpg", "image/jpeg"),
    "PNG": (".png", "image/png"),
    "WEBP": (".webp", "image/webp"),
}


class WorldCharacter(StrEnum):
    """The initial visual direction requested for a generated world."""

    VERDANT_KINGDOMS = "verdant_kingdoms"
    ASHEN_WILDS = "ashen_wilds"
    FROZEN_NORTH = "frozen_north"


class WorldSeedResponse(BaseModel):
    """Metadata returned after a seed image has been accepted."""

    seed_id: UUID
    original_name: str
    media_type: str
    width: int
    height: int
    size_bytes: int
    uploaded_at: datetime


class GenerationRequest(BaseModel):
    """Creative choices that will guide the terrain generator."""

    world_name: str | None = Field(default=None, max_length=80)
    character: WorldCharacter = WorldCharacter.VERDANT_KINGDOMS
    fate_seed: int | None = Field(default=None, ge=0, le=4_294_967_295)
    invert_land_and_sea: bool = False


class GenerationResponse(BaseModel):
    """A durable request that the terrain engine can process next."""

    generation_id: UUID
    seed_id: UUID
    status: str
    world_name: str | None
    character: WorldCharacter
    fate_seed: int
    invert_land_and_sea: bool
    created_at: datetime


def get_data_directory() -> Path:
    """Return the configurable directory used for local WorldWake data."""

    return Path(os.environ.get("WORLDWAKE_DATA_DIR", "data")).resolve()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    """Write metadata atomically so partial JSON files are never observed."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    temporary_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _read_json(path: Path, detail: str) -> dict[str, object]:
    """Load persisted JSON metadata or raise a structured API error."""

    if not path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored WorldSeed metadata could not be read.",
        ) from error


def _inspect_image(contents: bytes) -> tuple[str, str, int, int]:
    """Verify image bytes and return their normalized format information."""

    try:
        with Image.open(BytesIO(contents)) as image:
            width, height = image.size
            image_format = image.format

            if width * height > MAX_IMAGE_PIXELS:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Image dimensions are too large. Use at most 40 megapixels.",
                )

            image.verify()
    except HTTPException:
        raise
    except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a valid PNG, JPEG, WebP, or GIF image.",
        ) from error

    if image_format not in SUPPORTED_IMAGE_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a PNG, JPEG, WebP, or GIF image.",
        )

    extension, media_type = SUPPORTED_IMAGE_FORMATS[image_format]
    return extension, media_type, width, height


@router.post(
    "/world-seeds",
    response_model=WorldSeedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_world_seed(
    image: Annotated[UploadFile, File(description="The source shape or sketch")],
) -> WorldSeedResponse:
    """Validate and store an image that will become a generated world."""

    # Read the uploaded bytes once so the request can be validated and persisted
    # without leaving a partially stored file behind on failure.

    try:
        contents = await image.read(MAX_UPLOAD_BYTES + 1)
    finally:
        await image.close()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded image is empty.",
        )

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The image is too large. The maximum upload size is 15 MB.",
        )

    extension, media_type, width, height = _inspect_image(contents)
    seed_id = uuid4()
    uploaded_at = datetime.now(UTC)
    original_name = Path(image.filename or f"world-seed{extension}").name[:255]
    seed_directory = get_data_directory() / "world_seeds"
    image_path = seed_directory / f"{seed_id}{extension}"
    metadata_path = seed_directory / f"{seed_id}.json"

    seed_directory.mkdir(parents=True, exist_ok=True)
    image_path.write_bytes(contents)

    response = WorldSeedResponse(
        seed_id=seed_id,
        original_name=original_name,
        media_type=media_type,
        width=width,
        height=height,
        size_bytes=len(contents),
        uploaded_at=uploaded_at,
    )

    try:
        _write_json(
            metadata_path,
            {
                **response.model_dump(mode="json"),
                "stored_image": image_path.name,
            },
        )
    except OSError:
        image_path.unlink(missing_ok=True)
        raise

    return response


@router.get("/world-seeds/{seed_id}", response_model=WorldSeedResponse)
async def get_world_seed(seed_id: UUID) -> WorldSeedResponse:
    """Return metadata for a previously uploaded world seed."""

    metadata_path = get_data_directory() / "world_seeds" / f"{seed_id}.json"
    return WorldSeedResponse.model_validate(
        _read_json(metadata_path, "World seed not found.")
    )


@router.post(
    "/world-seeds/{seed_id}/generate",
    response_model=GenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_map_generation(
    seed_id: UUID,
    request: GenerationRequest,
) -> GenerationResponse:
    """Record a generation request for the upcoming terrain engine."""

    # Persist the request immediately so the generation workflow can be resumed
    # later, even before the visual engine has been connected.

    seed_metadata_path = (
        get_data_directory() / "world_seeds" / f"{seed_id}.json"
    )
    _read_json(seed_metadata_path, "World seed not found.")

    generation_id = uuid4()
    created_at = datetime.now(UTC)
    fate_seed = (
        request.fate_seed
        if request.fate_seed is not None
        else secrets.randbits(32)
    )
    response = GenerationResponse(
        generation_id=generation_id,
        seed_id=seed_id,
        status="awaiting_generator",
        world_name=request.world_name,
        character=request.character,
        fate_seed=fate_seed,
        invert_land_and_sea=request.invert_land_and_sea,
        created_at=created_at,
    )

    metadata_path = (
        get_data_directory()
        / "map_generations"
        / f"{generation_id}.json"
    )
    _write_json(metadata_path, response.model_dump(mode="json"))
    return response


@router.get(
    "/map-generations/{generation_id}",
    response_model=GenerationResponse,
)
async def get_map_generation(generation_id: UUID) -> GenerationResponse:
    """Return the current state of a map-generation request."""

    metadata_path = (
        get_data_directory()
        / "map_generations"
        / f"{generation_id}.json"
    )
    return GenerationResponse.model_validate(
        _read_json(metadata_path, "Map generation request not found.")
    )
