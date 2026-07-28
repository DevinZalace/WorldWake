"""Tests for the WorldSeed upload and generation request API."""

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from worldwake.main import app


client = TestClient(app)


def make_png() -> bytes:
    image = Image.new("L", (32, 24), color=255)
    image.paste(0, (6, 5, 26, 20))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_upload_and_request_generation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WORLDWAKE_DATA_DIR", str(tmp_path))

    upload_response = client.post(
        "/api/world-seeds",
        files={"image": ("ink-blot.png", make_png(), "image/png")},
    )

    assert upload_response.status_code == 201
    uploaded_seed = upload_response.json()
    assert uploaded_seed["original_name"] == "ink-blot.png"
    assert uploaded_seed["media_type"] == "image/png"
    assert uploaded_seed["width"] == 32
    assert uploaded_seed["height"] == 24

    generation_response = client.post(
        f"/api/world-seeds/{uploaded_seed['seed_id']}/generate",
        json={
            "world_name": "Mossmere",
            "character": "verdant_kingdoms",
            "fate_seed": 42,
            "invert_land_and_sea": False,
        },
    )

    assert generation_response.status_code == 202
    generation = generation_response.json()
    assert generation["seed_id"] == uploaded_seed["seed_id"]
    assert generation["status"] == "awaiting_generator"
    assert generation["world_name"] == "Mossmere"
    assert generation["fate_seed"] == 42

    status_response = client.get(
        f"/api/map-generations/{generation['generation_id']}"
    )
    assert status_response.status_code == 200
    assert status_response.json() == generation


def test_upload_rejects_non_image(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WORLDWAKE_DATA_DIR", str(tmp_path))

    response = client.post(
        "/api/world-seeds",
        files={"image": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 415
    assert response.json()["detail"].startswith("Upload a valid")


def test_generation_requires_existing_seed(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("WORLDWAKE_DATA_DIR", str(tmp_path))

    response = client.post(
        "/api/world-seeds/00000000-0000-0000-0000-000000000000/generate",
        json={},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "World seed not found."
