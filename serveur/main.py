import asyncio
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from game.decision_engine import simulate_story
from game.scenario_orchestrator import call_orchestrator_llm, generate_questions_for_context

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

COMMANDS: dict[str, list[str]] = {
    "clean": ["make", "-C", str(ROOT / "game"), "clean"],
    "fclean": ["make", "-C", str(ROOT), "fclean"],
    "data": ["make", "-C", str(ROOT / "data_part"), "all"],
    "setup": ["make", "-C", str(ROOT / "data_part"), "all"],
}


def build_run_command(args: list[str]) -> list[str]:
    n = "5"
    scenario = "default scenario"

    if args:
        first = args[0]
        if first.isdigit():
            n = first
            args = args[1:]
        else:
            scenario = first
            args = args[1:]

    if args:
        scenario = " ".join(args)

    return [
        str(ROOT / ".venv" / "bin" / "python"),
        str(ROOT / "game" / "game.py"),
        "--n",
        n,
        "--scenario",
        scenario,
    ]

MODELS_DIR = ROOT / "ml_part" / "out" / "models"
SELECTED_MODEL = "decision_model.keras"


def get_available_models() -> list[str]:
    if MODELS_DIR.exists():
        return sorted(f.name for f in MODELS_DIR.iterdir() if f.suffix == ".keras")
    return []


async def stream_process(cmd: list[str]):
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in process.stdout:
        text = line.decode(errors="replace").rstrip("\n")
        yield f"data: {text}\n\n"
    await process.wait()
    yield f"data: [exit {process.returncode}]\n\n"
    yield "data: __END__\n\n"


async def handle_model(args: list[str]):
    if args:
        model_name = args[0]
        available = get_available_models()
        if model_name in available:
            global SELECTED_MODEL
            SELECTED_MODEL = model_name
            yield f"data: ✓ model selected: {model_name}\n\n"
        else:
            yield f"data: ✗ unknown model: '{model_name}'\n\n"
            if available:
                yield "data: available models:\n\n"
                for m in available:
                    yield f"data:   {m}\n\n"
            else:
                yield "data: (no models trained yet — run 'data' then 'train' first)\n\n"
    else:
        available = get_available_models()
        yield f"data: current model: {SELECTED_MODEL}\n\n"
        if available:
            yield "data: available models:\n\n"
            for m in available:
                marker = "→ " if m == SELECTED_MODEL else "  "
                yield f"data:   {marker}{m}\n\n"
        else:
            yield "data: (no models trained yet — run 'data' then 'train' first)\n\n"
    yield "data: __END__\n\n"


@app.get("/scenario/questions")
async def scenario_questions(context: str = "simulation apocalypse il y a plus d'eau"):
    questions = call_orchestrator_llm(context, max_questions=5)
    return JSONResponse({"context": context, "questions": questions})


@app.post("/scenario/questions")
async def scenario_questions_post(payload: dict[str, Any]):
    context = str(payload.get("context", "simulation apocalypse il y a plus d'eau"))
    max_questions = int(payload.get("max_questions", 5))
    questions = call_orchestrator_llm(context, max_questions=max_questions)
    return JSONResponse({"context": context, "questions": questions})


@app.post("/scenario/run")
async def scenario_run(payload: dict[str, Any]):
    agents = payload.get("agents", [])
    if not agents:
        return JSONResponse({"error": "No agents provided."}, status_code=400)

    scenario = str(payload.get("scenario", "simulation default"))
    questions = call_orchestrator_llm(scenario, max_questions=int(payload.get("max_questions", 5)))

    story = simulate_story(agents, scenario, questions)

    result = {
        "scenario": scenario,
        "questions": questions,
        "story": {
            "kind": story.scenario_kind,
            "chapters": story.chapters,
            "survivor_count": story.survivor_count,
            "casualty_count": story.casualty_count,
            "outcomes": [
                {
                    "agent_id": outcome.agent_id,
                    "wealth": outcome.wealth,
                    "stability": outcome.stability,
                    "survived": outcome.survived,
                    "timeline": outcome.timeline,
                }
                for outcome in story.outcomes
            ],
            "ranking": [
                {
                    "position": position,
                    "agent_id": outcome.agent_id,
                    "wealth": outcome.wealth,
                    "stability": outcome.stability,
                    "survived": outcome.survived,
                }
                for position, outcome in enumerate(story.ranking, start=1)
            ],
        },
    }
    return JSONResponse(result)


@app.get("/exec/{command:path}")
async def exec_command(command: str):
    parts = command.split("/")
    base = parts[0]
    args = parts[1:]

    if base == "model":
        return StreamingResponse(
            handle_model(args),
            media_type="text/event-stream",
        )

    if base == "run":
        return StreamingResponse(
            stream_process(build_run_command(args)),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    if base not in COMMANDS:

        async def err():
            yield f"data: unknown command '{base}'. Available: {list(COMMANDS)}\n\n"
            yield "data: __END__\n\n"

        return StreamingResponse(err(), media_type="text/event-stream")
    return StreamingResponse(
        stream_process(COMMANDS[base]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
