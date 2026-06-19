"""Local dev server with reload limited to project source (not .venv)."""

from pathlib import Path

import uvicorn

SRC_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    uvicorn.run(
        "image_agent.api:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        reload_dirs=[str(SRC_DIR)],
    )


if __name__ == "__main__":
    main()
