from typing import Any

from scraper_engine.extraction import ElementExtractor
from scraper_engine.http import HTTPClient, HTTPRequest
from scraper_engine.parser import get_document
from scraper_engine.templating import TemplateRenderer
from scraper_engine.transforms import TransformerRegistry
from scraper_engine.workflow.context import ExecutionContext


def resolve_field_value(item: Any, field_path: str) -> Any:  # noqa: ANN401
    """Resolve a dot-separated field path from an item structure."""
    parts = field_path.split(".")
    current = item
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            res = []
            for elem in current:
                if isinstance(elem, dict) and part in elem:
                    val = elem[part]
                    if isinstance(val, list):
                        res.extend(val)
                    else:
                        res.append(val)
            current = res
        else:
            return None
    return current


class StepExecutor:
    """Executes an individual workflow step."""

    def __init__(self, http_client: HTTPClient) -> "StepExecutor":
        """Init.

        Args:
            http_client: The HTTP client to use for making requests.
        """
        self.http_client = http_client

    def _infer_default_selector_type(self, step_config: dict[str, Any], doc_type: str) -> str:
        """Infer default selector type based on step configuration or document type."""
        extract_cfg = step_config.get("extract")
        if extract_cfg and "selector_type" in extract_cfg:
            return extract_cfg["selector_type"]
        if doc_type.lower() == "json":
            return "jsonpath"
        return "css"

    def _extract_single_field(
        self,
        container: Any,  # noqa: ANN401
        field_cfg: dict[str, Any],
        default_sel_type: str = "css",
    ) -> Any:  # noqa: ANN401
        """Extract value(s) for a single non-nested field definition."""
        f_selector = field_cfg["selector"]
        f_sel_type = field_cfg.get("selector_type", default_sel_type)
        f_type = field_cfg.get("type", "text")
        f_attr = field_cfg.get("attribute")
        f_transforms = field_cfg.get("transform", [])

        extracted_vals = ElementExtractor.extract_field_values(
            root=container,
            selector=f_selector,
            selector_type=f_sel_type,
            extraction_type=f_type,
            attribute=f_attr,
        )

        if f_transforms:
            extracted_vals = TransformerRegistry.apply_pipeline(extracted_vals, f_transforms)

        if len(extracted_vals) == 0:
            return None
        if len(extracted_vals) == 1:
            return extracted_vals[0]
        return extracted_vals

    def _extract_nested_field(
        self,
        container: Any,  # noqa: ANN401
        field_cfg: dict[str, Any],
        default_sel_type: str = "css",
    ) -> list[dict[str, Any]]:
        """Extract list of dicts for a nested field definition."""
        sub_fields = field_cfg["fields"]
        extract_cfg = field_cfg.get("extract")
        if extract_cfg:
            sub_selector = extract_cfg["selector"]
            sub_sel_type = extract_cfg.get("selector_type", default_sel_type)
        elif "selector" in field_cfg:
            sub_selector = field_cfg["selector"]
            sub_sel_type = field_cfg.get("selector_type", default_sel_type)
        else:
            sub_selector = None
            sub_sel_type = default_sel_type

        if sub_selector:
            sub_containers = ElementExtractor.extract_nodes(container, sub_selector, sub_sel_type)
        else:
            sub_containers = [container]

        return [
            self._extract_fields_from_container(sub_c, sub_fields, default_sel_type)
            for sub_c in sub_containers
        ]

    def _extract_fields_from_container(
        self,
        container: Any,  # noqa: ANN401
        fields_config: dict[str, Any],
        default_sel_type: str = "css",
    ) -> dict[str, Any]:
        """Extract fields from a container node, handling nested field definitions recursively."""
        item_data: dict[str, Any] = {}
        for field_name, field_cfg in fields_config.items():
            if "fields" in field_cfg:
                item_data[field_name] = self._extract_nested_field(container, field_cfg, default_sel_type)
            else:
                item_data[field_name] = self._extract_single_field(container, field_cfg, default_sel_type)
        return item_data

    def _determine_document_type(self, step_config: dict[str, Any], response: Any) -> str:  # noqa: ANN401
        """Determine document parser type from step config, response headers, or content."""
        req_config = step_config.get("request", {})
        if "response_type" in req_config:
            return req_config["response_type"]
        if "parser" in step_config:
            return step_config["parser"]

        extract_cfg = step_config.get("extract", {})
        if extract_cfg.get("selector_type") in ("jsonpath", "json"):
            return "json"

        # Check response content type header if available
        headers = getattr(response, "headers", {})
        is_dict_or_has_get = isinstance(headers, dict) or hasattr(headers, "get")
        content_type = headers.get("content-type", "").lower() if is_dict_or_has_get else ""
        if "application/json" in content_type:
            return "json"

        # Content sniffing
        text = response.text.strip() if hasattr(response, "text") else ""
        if (text.startswith("{") and text.endswith("}")) or (text.startswith("[") and text.endswith("]")):
            try:
                import json  # noqa: PLC0415
                json.loads(text)
            except ValueError:
                pass
            else:
                return "json"

        return "html"

    def execute_single_request(self, step_config: dict[str, Any], context: ExecutionContext) -> list[dict[str, Any]]:
        """Execute a single request for a workflow step."""
        tpl_ctx = context.get_template_context()

        req_config = step_config.get("request")
        if not req_config:
            return []

        rendered_url = TemplateRenderer.render_string(req_config["url"], tpl_ctx)
        method = req_config.get("method", "GET").upper()
        headers = TemplateRenderer.render_data(req_config.get("headers", {}), tpl_ctx)
        params = TemplateRenderer.render_data(req_config.get("params", {}), tpl_ctx)

        request = HTTPRequest(
            url=rendered_url,
            method=method,
            headers=headers,
            params=params,
        )

        response = self.http_client.send(request)
        doc_type = self._determine_document_type(step_config, response)
        doc = get_document(response.text, doc_type)

        default_sel_type = self._infer_default_selector_type(step_config, doc_type)

        extract_config = step_config.get("extract")
        fields_config = step_config.get("fields", {})

        if extract_config:
            selector = extract_config["selector"]
            selector_type = extract_config.get("selector_type", default_sel_type)
            containers = ElementExtractor.extract_nodes(doc, selector, selector_type)
        else:
            containers = [doc]

        results: list[dict[str, Any]] = []

        for container in containers:
            if isinstance(container, dict) and not fields_config:
                results.append(container)
            else:
                item_data = self._extract_fields_from_container(container, fields_config, default_sel_type)
                results.append(item_data)

        return results

    def _execute_for_each_sub_item(
        self,
        step_config: dict[str, Any],
        context: ExecutionContext,
        item: dict[str, Any],
        sub_item: Any,  # noqa: ANN401
        sub_field: str | None,
    ) -> list[dict[str, Any]]:
        """Execute step request for a single sub-item in for_each loop."""
        loop_ctx: dict[str, Any] = dict(item)
        if isinstance(sub_item, dict):
            loop_ctx.update(sub_item)
            if "value" in sub_item:
                loop_ctx["value"] = sub_item["value"]
            elif sub_field and sub_field in sub_item:
                loop_ctx["value"] = sub_item[sub_field]
            elif "id" in sub_item:
                loop_ctx["value"] = sub_item["id"]
            elif "sub_id" in sub_item:
                loop_ctx["value"] = sub_item["sub_id"]
            else:
                loop_ctx["value"] = sub_item
        else:
            loop_ctx["value"] = sub_item

        context.push_loop_context(loop_ctx)
        try:
            res_list = self.execute_single_request(step_config, context)
            sub_results: list[dict[str, Any]] = []
            for r in res_list:
                merged = dict(item)
                if isinstance(sub_item, dict):
                    merged.update(sub_item)
                merged.update(r)
                sub_results.append(merged)
            return sub_results
        finally:
            context.pop_loop_context()

    def _execute_for_each(
        self,
        step_config: dict[str, Any],
        context: ExecutionContext,
        for_each_cfg: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute step using for_each loop over step results."""
        from_step_id = for_each_cfg["from"]
        from_field = for_each_cfg.get("field")
        sub_field = for_each_cfg.get("sub_field")
        items = context.get_step_result(from_step_id)

        step_results: list[dict[str, Any]] = []

        for item in items:
            field_val = resolve_field_value(item, from_field) if from_field else None

            if isinstance(field_val, list):
                for sub_item in field_val:
                    step_results.extend(
                        self._execute_for_each_sub_item(step_config, context, item, sub_item, sub_field),
                    )
            else:
                target_val = field_val if from_field else item
                if isinstance(target_val, list):
                    for sub_item in target_val:
                        step_results.extend(
                            self._execute_for_each_sub_item(step_config, context, item, sub_item, sub_field),
                        )
                else:
                    step_results.extend(
                        self._execute_for_each_sub_item(step_config, context, item, target_val, sub_field),
                    )

        return step_results

    def execute(self, step_config: dict[str, Any], context: ExecutionContext) -> list[dict[str, Any]]:
        """Execute a single workflow step."""
        step_id = step_config["id"]
        for_each_cfg = step_config.get("for_each")

        if for_each_cfg:
            step_results = self._execute_for_each(step_config, context, for_each_cfg)
        else:
            step_results = self.execute_single_request(step_config, context)

        context.set_step_result(step_id, step_results)
        return step_results


class WorkflowEngine:
    """Orchestrates execution of workflow steps."""

    def __init__(self, http_client: HTTPClient) -> "WorkflowEngine":
        """Init.

        Args:
            http_client: The HTTP client to use for making requests.
        """
        self.http_client = http_client
        self.step_executor = StepExecutor(http_client)

    def run(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute a workflow.

        Args:
            config: The workflow configuration.

        """
        variables = config.get("variables", {})
        context = ExecutionContext(variables=variables)

        last_results: list[dict[str, Any]] = []

        for step_config in config.get("steps", []):
            last_results = self.step_executor.execute(step_config, context)

        return last_results
