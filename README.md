# GameOfLife

A multi-component project that models demographic profiles using real census data and machine learning. Agents are sampled from population profiles built on the UCI Adult Income dataset, and their attributes are served through a FastAPI backend to a React terminal frontend.

## Architecture

```
data_part/ ──► ml_part/ ──► game/ ──► serveur/ ──► Client/
  UCI data     TF model    agents    FastAPI      React UI
```

**Pipeline:**
1. `data_part` processes the UCI Adult Income dataset into demographic profiles (`out_profiles.csv`)
2. `ml_part` trains a neural network to predict an agent's decision score
3. `game` samples agents from those profiles (`agents.json`)
4. `serveur` exposes pipeline commands via a streaming REST API
5. `Client` provides a terminal UI to trigger and observe pipeline steps

## Quickstart

```bash
# One-time bootstrap: creates/refreshes the shared Python 3.11 virtualenv
make setup

# One-time bootstrap for the React client
cd Client && pnpm install
```

```bash
# Optional: enable cloud question generation through Ollama.
cp serveur/.env.example serveur/.env
# Then set OLLAMA_KEY in serveur/.env (never commit this file).
```

```bash
# Terminal 1 — run the full pipeline (data → ml → agents)
make all

# Terminal 2 — start FastAPI and Vite together (blocks)
make dev
```

## Components

### data_part — Data Pipeline

Reads the UCI Adult Income dataset (`Data/train.csv`) and produces:

- `out/out_profiles.csv` — one row per (race × age) group: modal features, capital gain mean, income rate
- `out/out_*.csv` — per-feature distribution files (education, marital status, occupation, relationship, race)

```bash
cd data_part && make all
```

### ml_part — ML Model

Trains a binary classifier to predict whether an agent takes a "proactive" life action.

- **Input:** 5 categorical features (race, education, marital status, occupation, relationship) + 3 numeric (age, sample size, capital gain)
- **Architecture:** Dense(64) → Dropout(0.2) → Dense(32) → sigmoid output
- **Outputs:** `out/models/decision_model.keras`, `out/models/preprocessor.joblib`

```bash
cd ml_part && make all
```

### game — Agent Sampling

Samples N agents directly from `out_profiles.csv` and writes `agents.json`.

```bash
cd game && make run
# or with options:
python game.py --n 10 --seed 0 --out agents.json
```

### serveur — Backend API

FastAPI server that streams pipeline command output to the frontend via SSE.
It reads the optional Ollama configuration from `serveur/.env`; without `OLLAMA_KEY`,
the simulation uses its local question generator.

| Endpoint | Action |
|---|---|
| `GET /exec/setup` | run data pipeline |
| `GET /exec/run` | sample agents |
| `GET /exec/data` | rerun data pipeline |
| `GET /exec/clean` | remove generated game files |
| `GET /exec/fclean` | clean entire project |

```bash
cd serveur && make run   # starts uvicorn at http://localhost:8000
```

### Client — React Frontend

Terminal UI built with Vite + React 19 + TypeScript. Connects to the backend via the Vite proxy (`/exec → http://localhost:8000`).

```bash
cd Client && pnpm install && pnpm dev
```

Available commands in the terminal:

| Command | Description |
|---|---|
| `setup` | run the data pipeline |
| `run` | sample agents from profiles |
| `data` | rerun the data pipeline |
| `clean` | remove generated game files |
| `fclean` | clean the entire project |
| `clear` | clear the terminal |
| `help` | show available commands |

## Data

The project uses the [UCI Adult Income dataset](https://archive.ics.uci.edu/dataset/2/adult). Place `train.csv` in `data_part/Data/` before running the data pipeline. A preprocessed version is included in `data_part.zip`.

## Stack

| Component | Technology |
|---|---|
| Data processing | Python, pandas |
| ML | TensorFlow/Keras, scikit-learn |
| Agent sampling | Python |
| API | FastAPI, uvicorn |
| Frontend | React 19, TypeScript, Vite |

## Requirements

- Python 3.11
- Node.js + pnpm
- One shared virtual environment lives at `./.venv`
