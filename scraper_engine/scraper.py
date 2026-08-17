from typing import Any

from scraper_engine.config import ConfigLoader
from scraper_engine.http import HTTPClient, HTTPXClient
from scraper_engine.workflow import WorkflowEngine


class Scraper:
    """Main entry point for running scraper engine tasks."""

    def __init__(
        self,
        config: dict[str, Any] | str,
        http_client: HTTPClient | None = None,
    ) -> None:
        """Init.

        Args:
        config: The workflow configuration.
        http_client: The HTTP client to use for making requests.
        """
        if isinstance(config, str):
            if config.strip().startswith("{"):
                self.config = ConfigLoader.load_from_json(config)
            else:
                self.config = ConfigLoader.load_from_file(config)
        elif isinstance(config, dict):
            self.config = ConfigLoader.load_from_dict(config)
        else:
            msg = "Config must be a dict, JSON string, or file path."
            raise TypeError(msg)

        self._custom_http_client = http_client is not None
        self.http_client = http_client or HTTPXClient()
        self.engine = WorkflowEngine(self.http_client)

    def run(self) -> list[dict[str, Any]]:
        """Run the scraper engine workflow."""
        try:
            return self.engine.run(self.config)
        finally:
            if not self._custom_http_client:
                self.http_client.close()
