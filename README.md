# WorldWake

WorldWake is a campaign-world engine for tabletop RPGs.

The idea began with a problem from my own campaigns: notes are good at recording what the players did, but not what happened elsewhere while they were traveling, resting, or ignoring a growing problem.

WorldWake is being built to remember the world between sessions. Roads can become unsafe, factions can gain resources, settlements can change, and those changes should have understandable causes.

## Current state

The current application includes:

- Account registration and login
- Argon2id password hashing
- Database-backed 30-day sessions
- CSRF-protected account actions
- Password changes with session rotation
- Authentication rate limiting
- A WorldSeed prototype for validating and storing uploaded map references
- Automated tests for authentication, database behavior, and WorldSeed APIs

WorldSeed does not generate finished maps yet. The current milestone establishes the account, upload, and persistence foundations that later map and campaign systems will use.

## Technology

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- SQLite
- Pydantic
- Pillow
- Pytest
- Vanilla JavaScript and CSS

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --editable ".[dev]"
alembic upgrade head
fastapi dev src/worldwake/main.py
