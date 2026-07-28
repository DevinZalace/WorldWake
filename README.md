# WorldWake

> **Create a world. Chronicle its history. Watch it awaken.**

WorldWake is an open-source fantasy world simulation platform designed for tabletop RPGs, novels, and other fictional worlds. Instead of acting as a passive campaign wiki, WorldWake aims to become a living world engine that remembers player actions, simulates events beyond the party's view, and visualizes history across an interactive map.

The long-term vision is divided into three major systems:

- **WorldSeed** – Create and shape fantasy worlds from sketches, maps, or prompts.
- **Chronicle** – Convert campaign notes into structured historical events and geographic movement.
- **WorldTurn** – Advance the world through time by simulating factions, trade, politics, resources, and the consequences of player actions.

---

# Current Status

 **Early Development**

The project is currently focused on building the foundation for **WorldSeed**.

The first prototype includes:

- Modern Python project structure
- FastAPI backend
- Interactive browser interface
- Local image upload
- Instant image preview

Future milestones will progressively transform an uploaded sketch into a structured fantasy world.

---

# Project Vision

Imagine uploading:

- a hand-drawn continent
- a county boundary
- a napkin sketch
- an ink blot
- or an existing fantasy map

Then describing the world you imagine:

> "A cold northern kingdom with ancient dragon ruins. A massive mountain range divides the continent. The capital is named Kingsfall."

WorldWake interprets those ideas and begins constructing a believable fantasy world.

Eventually that world becomes more than artwork.

It becomes a simulation.

Roads influence trade.

Trade influences settlements.

Settlements influence kingdoms.

Kingdoms influence politics.

Player actions influence everything.

Every major change should be explainable through a visible chain of consequences.

---

# Planned Features

## 🌍 WorldSeed

- Upload hand-drawn maps
- Upload geographic boundaries
- AI-assisted terrain generation
- Fantasy map styling
- Settlement placement
- Rivers and road generation
- Region creation
- Interactive editing
- Multiple generated world drafts
- "Surprise Me" generation mode

---

## 📜 Chronicle

- Upload campaign notes
- Extract locations and events
- Reconstruct party travel
- Build historical timelines
- Detect ambiguous locations
- Interactive event confirmation
- Character and faction tracking

---

## ⏳ WorldTurn

- Advance fictional time
- Simulate faction behavior
- Resource production and consumption
- Trade network simulation
- Political changes
- Military movement
- Dynamic rumors
- World consequence tracking
- Fully explainable event ancestry

Example:

```text
Food prices increased
└── Grain shipments declined
    └── Southern bridge collapsed
        └── Players destroyed bridge during Session 8
```

The world remembers.

---

# Technology Stack

## Current

- Python 3.12+
- FastAPI
- HTML
- CSS
- JavaScript

## Planned

- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- NetworkX
- Leaflet
- Pytest
- Docker
- GitHub Actions
- Amazon Web Services (AWS)

---

# Repository Structure

```text
WorldWake/
├── prototypes/
│   └── consequence_engine.py
├── src/
│   └── worldwake/
│       ├── static/
│       ├── __init__.py
│       └── main.py
├── data/
├── pyproject.toml
├── README.md
└── .gitignore
```

---

# Getting Started

Clone the repository:

```bash
git clone https://github.com/DevinZalace/WorldWake.git
cd WorldWake
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

### Linux / macOS / WSL

```bash
source .venv/bin/activate
```

Install the project in editable mode:

```bash
python -m pip install --upgrade pip
python -m pip install --editable .
```

Run the development server:

```bash
fastapi dev src/worldwake/main.py
```

Open your browser:

```text
http://127.0.0.1:8000
```

---

# Development Roadmap

## Phase 1
- [x] Initialize project
- [x] Create FastAPI application
- [x] Build first WorldSeed interface
- [x] Local image preview
- [ ] Upload image to backend
- [ ] Save uploaded projects

## Phase 2
- [ ] Interpret uploaded maps
- [ ] Generate structured world data
- [ ] Place settlements
- [ ] Generate terrain
- [ ] Interactive editing

## Phase 3
- [ ] Chronicle campaign notes
- [ ] Interactive timelines
- [ ] Route reconstruction

## Phase 4
- [ ] World simulation
- [ ] Faction AI
- [ ] Resource economy
- [ ] Consequence engine
- [ ] Living atlas

---

# Why WorldWake?

Most campaign managers excel at storing information.

WorldWake aims to answer a different question:

> **What happened while the party was somewhere else?**

By combining geography, history, simulation, and AI-assisted interpretation, WorldWake strives to become a living fantasy world that evolves alongside every campaign.

---

# License

License to be determined.
