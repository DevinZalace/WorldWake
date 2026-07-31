# WorldWake

> Create a world. Chronicle its history. Watch it awaken.

WorldWake is an early-stage fantasy world-generation project for tabletop RPGs and fictional settings.

Development currently focuses on **WorldSeed**, a FastAPI service that accepts map sketches or source images and prepares them for a future terrain-generation system.

## Current Capabilities

- Browser interface for selecting and previewing an image
- Upload and validation of PNG, JPEG, WebP, and GIF images
- Local storage of images and JSON metadata
- Retrieval of previously uploaded world seeds
- Creation and tracking of map-generation requests
- Configurable world name, visual character, random seed, and land/sea inversion

WorldWake does **not** generate finished maps yet. Generation requests are currently stored with an `awaiting_generator` status while the terrain engine is developed.

## Technology

- Python 3.12+
- FastAPI
- Pydantic
- Pillow
- HTML, CSS, and JavaScript

## Running Locally

```bash
git clone https://github.com/DevinZalace/WorldWake.git
cd WorldWake

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install --editable .

fastapi dev src/worldwake/main.py
```

Open `http://127.0.0.1:8000` in your browser.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/world-seeds` | Upload and validate a source image |
| `GET` | `/api/world-seeds/{seed_id}` | Retrieve uploaded-image metadata |
| `POST` | `/api/world-seeds/{seed_id}/generate` | Create a map-generation request |
| `GET` | `/api/map-generations/{generation_id}` | Retrieve generation status |

## Next Steps

- Connect the complete browser workflow to the backend
- Build the first terrain-generation engine
- Display and edit generated map results
