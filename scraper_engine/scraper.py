from typing import Dict, Any, List, Union, Optional

from scraper_engine.config import ConfigLoader
from scraper_engine.http import HTTPClient, HTTPXClient
from scraper_engine.workflow import WorkflowEngine


class Scraper:
    """Main entry point for running scraper engine tasks."""

    def __init__(
        self,
        config: Union[Dict[str, Any], str],
        http_client: Optional[HTTPClient] = None
    ):
        if isinstance(config, str):
            if config.strip().startswith("{"):
                self.config = ConfigLoader.load_from_json(config)
            else:
                self.config = ConfigLoader.load_from_file(config)
        elif isinstance(config, dict):
            self.config = ConfigLoader.load_from_dict(config)
        else:
            raise TypeError("Config must be a dict, JSON string, or file path.")

        self._custom_http_client = http_client is not None
        self.http_client = http_client or HTTPXClient()
        self.engine = WorkflowEngine(self.http_client)

    def run(self) -> List[Dict[str, Any]]:
        try:
            return self.engine.run(self.config)
        finally:
            if not self._custom_http_client:
                self.http_client.close()
