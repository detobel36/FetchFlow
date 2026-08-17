from typing import Any

from scraper_engine.extraction import ElementExtractor
from scraper_engine.http import HTTPClient, HTTPRequest
from scraper_engine.parser import HTMLDocument
from scraper_engine.templating import TemplateRenderer
from scraper_engine.transforms import TransformerRegistry
from scraper_engine.workflow.context import ExecutionContext


class StepExecutor:
    """Executes an individual workflow step."""

    def __init__(self, http_client: HTTPClient) -> "StepExecutor":
        """Init.

        Args:
        http_client: The HTTP client to use for making requests.
        """
        self.http_client = http_client

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
        doc = HTMLDocument(response.text)

        extract_config = step_config.get("extract")
        fields_config = step_config.get("fields", {})

        if extract_config:
            selector = extract_config["selector"]
            selector_type = extract_config.get("selector_type", "css")
            containers = ElementExtractor.extract_nodes(doc, selector, selector_type)
        else:
            containers = [doc]

        results: list[dict[str, Any]] = []

        for container in containers:
            item_data: dict[str, Any] = {}
            for field_name, field_cfg in fields_config.items():
                f_selector = field_cfg["selector"]
                f_sel_type = field_cfg.get("selector_type", "css")
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
                    item_data[field_name] = None
                elif len(extracted_vals) == 1:
                    item_data[field_name] = extracted_vals[0]
                else:
                    item_data[field_name] = extracted_vals

            results.append(item_data)

        return results

    def execute(self, step_config: dict[str, Any], context: ExecutionContext) -> list[dict[str, Any]]:
        """Execute a single workflow step."""
        step_id = step_config["id"]
        for_each_cfg = step_config.get("for_each")

        if for_each_cfg:
            from_step_id = for_each_cfg["from"]
            from_field = for_each_cfg.get("field")
            items = context.get_step_result(from_step_id)

            step_results: list[dict[str, Any]] = []

            for item in items:
                loop_ctx: dict[str, Any] = dict(item)
                if from_field and from_field in item:
                    loop_ctx["value"] = item[from_field]
                elif from_field:
                    loop_ctx["value"] = None

                context.push_loop_context(loop_ctx)
                try:
                    res_list = self.execute_single_request(step_config, context)
                    for r in res_list:
                        # Combine loop item context with newly extracted fields
                        merged = dict(item)
                        merged.update(r)
                        step_results.append(merged)
                finally:
                    context.pop_loop_context()

            context.set_step_result(step_id, step_results)
            return step_results
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
