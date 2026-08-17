import argparse
import json
import sys
from pathlib import Path

from scraper_engine.errors import ScraperEngineError
from scraper_engine.scraper import Scraper


def main(args: list[str] | None = None) -> int:
    """Entry point for the scraper engine CLI."""
    parser = argparse.ArgumentParser(
        description="Run web scrapers configured via JSON specifications.",
    )
    parser.add_argument(
        "config",
        help="Path to JSON configuration file or raw JSON string",
    )
    parser.add_argument(
        "-o", "--output",
        help="Path to output JSON file (default: print to stdout)",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON output indentation level (default: 2)",
    )

    parsed_args = parser.parse_args(args)

    try:
        scraper = Scraper(parsed_args.config)
        results = scraper.run()
        output_data = json.dumps(results, indent=parsed_args.indent, ensure_ascii=False)

        if parsed_args.output:
            with Path.open(parsed_args.output, "w", encoding="utf-8") as f:
                f.write(output_data)
                f.write("\n")
    except ScraperEngineError as e:
        sys.stderr.write(f"Error executing scraper: {e}\n")
        return 1
    except Exception as e: # noqa: BLE001
        sys.stderr.write(f"Unexpected error: {e}\n")
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
