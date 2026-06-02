import asyncio
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ROOT = Path(__file__).resolve().parent.parent

COMMANDS: dict[str, list[str]] = {
    "run":    ["make", "-C", str(ROOT / "game"),      "run"],
    "clean":  ["make", "-C", str(ROOT / "game"),      "clean"],
    "fclean": ["make", "-C", str(ROOT),               "fclean"],
    "data":   ["make", "-C", str(ROOT / "data_part"), "all"],
    "setup":  ["make", "-C", str(ROOT / "data_part"), "all"],
}


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


@app.get("/exec/{command}")
async def exec_command(command: str):
    if command not in COMMANDS:
        async def err():
            yield f"data: unknown command '{command}'. Available: {list(COMMANDS)}\n\n"
            yield "data: __END__\n\n"
        return StreamingResponse(err(), media_type="text/event-stream")
    return StreamingResponse(
        stream_process(COMMANDS[command]),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
