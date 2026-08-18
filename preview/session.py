import json
from typing import Any

from preview.html_highlighter import highlight_html_elements
from preview.validation import find_key_line_number, validate_scraper_json
from scraper_engine.http import HTTPClient, HTTPXClient
from scraper_engine.workflow.context import ExecutionContext
from scraper_engine.workflow.engine import StepExecutor


class DebugSession:
    """Manages debug state, step execution, history caching, and loop iteration state."""

    def __init__(
        self,
        json_config: str | dict[str, Any] | None = None,
        http_client: HTTPClient | None = None,
    ) -> None:
        """Init DebugSession."""
        self.http_client = http_client or HTTPXClient()
        self.step_executor = StepExecutor(self.http_client)

        self.raw_json: str = ""
        self.config: dict[str, Any] | None = None
        self.validation_result: dict[str, Any] = {"valid": False, "syntax_error": None, "schema_errors": []}

        self.execution_context: ExecutionContext | None = None
        self.steps_config: list[dict[str, Any]] = []

        self.current_step_index: int = 0
        self.current_iteration_index: int = 0

        # Execution history map: key = (step_index, iteration_index) -> trace_dict
        self.history: dict[tuple[int, int], dict[str, Any]] = {}

        if json_config:
            if isinstance(json_config, dict):
                self.load_config(json.dumps(json_config, indent=2))
            else:
                self.load_config(str(json_config))

    def load_config(self, json_str: str) -> dict[str, Any]:
        """Update and validate JSON configuration."""
        self.raw_json = json_str
        val_res = validate_scraper_json(json_str)
        self.validation_result = val_res

        if val_res["valid"] and val_res["config"]:
            self.config = val_res["config"]
            self.steps_config = self.config.get("steps", [])
        else:
            self.config = None
            self.steps_config = []

        return self.validation_result

    def start(self) -> dict[str, Any]:
        """Start or restart the debug session from Step 0."""
        if not self.raw_json:
            msg = "No JSON configuration loaded."
            raise ValueError(msg)

        val = self.load_config(self.raw_json)
        if not val["valid"] or not self.config:
            return self.get_state()

        variables = self.config.get("variables", {})
        self.execution_context = ExecutionContext(variables=variables)

        self.history.clear()
        self.current_step_index = 0
        self.current_iteration_index = 0

        if self.steps_config:
            self._execute_step_and_cache(0)

        return self.get_state()

    def restart(self) -> dict[str, Any]:
        """Reset debug session and start over from first step."""
        return self.start()

    def _execute_step_and_cache(self, step_idx: int) -> None:
        """Execute step at step_idx using real scraper engine and store traces in history."""
        if not self.config or not self.execution_context or step_idx >= len(self.steps_config):
            return

        step_cfg = self.steps_config[step_idx]

        try:
            _results, traces = self.step_executor.execute_with_trace(step_cfg, self.execution_context)
            for trace in traces:
                iter_idx = trace.get("iteration_index", 0)
                self.history[(step_idx, iter_idx)] = trace
        except Exception as err:  # noqa: BLE001
            error_trace = {
                "step_id": step_cfg.get("id"),
                "iteration_index": 0,
                "total_iterations": 1,
                "loop_context": {},
                "request": step_cfg.get("request"),
                "response": None,
                "doc_type": "none",
                "extract": None,
                "fields": {},
                "results": [],
                "error": f"Execution error: {err}",
            }
            self.history[(step_idx, 0)] = error_trace

    def next(self) -> dict[str, Any]:
        """Advance to next operation (iteration or step)."""
        if not self.config or not self.steps_config:
            return self.get_state()

        current_key = (self.current_step_index, self.current_iteration_index)
        current_trace = self.history.get(current_key)

        total_iters = current_trace.get("total_iterations", 1) if current_trace else 1

        if self.current_iteration_index + 1 < total_iters:
            self.current_iteration_index += 1
            if (self.current_step_index, self.current_iteration_index) not in self.history:
                self._execute_step_and_cache(self.current_step_index)
            return self.get_state()

        if self.current_step_index + 1 < len(self.steps_config):
            self.current_step_index += 1
            self.current_iteration_index = 0
            if (self.current_step_index, 0) not in self.history:
                self._execute_step_and_cache(self.current_step_index)

        return self.get_state()

    def previous(self) -> dict[str, Any]:
        """Navigate backward to previous operation without making HTTP requests."""
        if self.current_iteration_index > 0:
            self.current_iteration_index -= 1
            return self.get_state()

        if self.current_step_index > 0:
            self.current_step_index -= 1
            prev_iters = [iter_idx for (s_idx, iter_idx) in self.history if s_idx == self.current_step_index]
            self.current_iteration_index = max(prev_iters) if prev_iters else 0

        return self.get_state()

    def next_iteration(self) -> dict[str, Any]:
        """Navigate to next loop iteration within current step."""
        current_key = (self.current_step_index, self.current_iteration_index)
        current_trace = self.history.get(current_key)
        total_iters = current_trace.get("total_iterations", 1) if current_trace else 1

        if self.current_iteration_index + 1 < total_iters:
            self.current_iteration_index += 1
            if (self.current_step_index, self.current_iteration_index) not in self.history:
                self._execute_step_and_cache(self.current_step_index)

        return self.get_state()

    def previous_iteration(self) -> dict[str, Any]:
        """Navigate to previous loop iteration within current step."""
        if self.current_iteration_index > 0:
            self.current_iteration_index -= 1

        return self.get_state()

    def rerun_current_step(self) -> dict[str, Any]:
        """Re-run active step with current JSON configuration using existing execution context."""
        if not self.config or not self.execution_context or self.current_step_index >= len(self.steps_config):
            return self.get_state()

        val = self.load_config(self.raw_json)
        if not val["valid"]:
            return self.get_state()

        keys_to_remove = [k for k in self.history if k[0] >= self.current_step_index]
        for k in keys_to_remove:
            del self.history[k]

        self._execute_step_and_cache(self.current_step_index)
        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        """Construct full state response object for the UI."""
        total_steps = len(self.steps_config)
        step_cfg = self.steps_config[self.current_step_index] if 0 <= self.current_step_index < total_steps else None
        step_id = step_cfg.get("id", "") if step_cfg else ""

        line_number = find_key_line_number(self.raw_json, ["steps", step_id]) if step_id else 1

        active_key = (self.current_step_index, self.current_iteration_index)
        trace = self.history.get(active_key)

        highlighted_html = None
        if trace and trace.get("doc_type") == "html" and trace.get("response"):
            raw_html = trace["response"].get("text", "")
            ext_cfg = trace.get("extract", {})
            container_sel = ext_cfg.get("selector") if ext_cfg else None
            container_sel_type = ext_cfg.get("selector_type", "css") if ext_cfg else "css"
            fields_cfg = step_cfg.get("fields") if step_cfg else None
            req_url = trace.get("request", {}).get("url") if trace.get("request") else None

            highlighted_html = highlight_html_elements(
                html_content=raw_html,
                container_selector=container_sel,
                container_selector_type=container_sel_type,
                fields_config=fields_cfg,
                base_url=req_url,
            )

        return {
            "validation": self.validation_result,
            "current_step_index": self.current_step_index,
            "total_steps": total_steps,
            "step_id": step_id,
            "step_config": step_cfg,
            "line_number": line_number,
            "current_iteration_index": self.current_iteration_index,
            "total_iterations": trace.get("total_iterations", 1) if trace else 1,
            "loop_context": trace.get("loop_context", {}) if trace else {},
            "request": trace.get("request") if trace else None,
            "response": trace.get("response") if trace else None,
            "doc_type": trace.get("doc_type", "none") if trace else "none",
            "extract": trace.get("extract") if trace else None,
            "fields": trace.get("fields", {}) if trace else {},
            "results": trace.get("results", []) if trace else [],
            "error": trace.get("error") if trace else None,
            "highlighted_html": highlighted_html,
            "raw_html": trace["response"].get("text", "") if trace and trace.get("response") else "",
        }
