import argparse
from pathlib import Path

import uvicorn

from preview.app import app, session


def main() -> None:
    """CLI entrypoint for Scraper Preview & Debugger."""
    parser = argparse.ArgumentParser(description="Scraper Preview & Debugger visual tool.")
    parser.add_argument("config", nargs="?", help="Path to initial JSON scraper configuration file.")
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host address to bind preview server (default: 127.0.0.1).",
    )
    parser.add_argument("--port", type=int, default=8000, help="Port to bind preview server (default: 8000).")

    args = parser.parse_args()

    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            print(f"Loading initial configuration from: {config_path}")  # noqa: T201
            raw_json = config_path.read_text(encoding="utf-8")
            session.load_config(raw_json)
        else:
            print(f"Warning: Configuration file not found at '{config_path}'")  # noqa: T201

    print(f"Starting Scraper Preview & Debugger on http://{args.host}:{args.port}")  # noqa: T201
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
