import logging
from typing import Any

import lxml.html

from scraper_engine.parser import get_selector_engine

logger = logging.getLogger(__name__)

INJECTED_PREVIEW_STYLES = """
<style id="debugger-preview-styles">
  [data-debugger-container="true"] {
    outline: 2px solid #3182ce !important;
    outline-offset: -1px !important;
    background-color: rgba(49, 130, 206, 0.1) !important;
    position: relative !important;
  }
  [data-debugger-field] {
    outline: 2px dashed #38a169 !important;
    outline-offset: -1px !important;
    background-color: rgba(56, 161, 105, 0.18) !important;
  }
  .debugger-tooltip-badge {
    position: absolute;
    top: -22px;
    left: 0;
    background: #2b6cb0;
    color: #ffffff;
    font-size: 11px;
    font-family: monospace;
    padding: 2px 6px;
    border-radius: 3px;
    z-index: 99999;
    pointer-events: none;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    white-space: nowrap;
  }
</style>
<script id="debugger-preview-script">
  document.addEventListener("mouseover", function(e) {
    var target = e.target.closest("[data-debugger-field], [data-debugger-container='true']");
    if (!target) return;
    var existing = document.querySelector(".debugger-tooltip-badge");
    if (existing) existing.remove();
    var badge = document.createElement("div");
    badge.className = "debugger-tooltip-badge";
    if (target.dataset.debuggerField) {
      badge.textContent = "Field: " + target.dataset.debuggerField + " (" + target.dataset.debuggerFieldSelector + ")";
    } else if (target.dataset.debuggerSelector) {
      badge.textContent = "Container: " + target.dataset.debuggerSelector;
    }
    target.appendChild(badge);
  });
  document.addEventListener("mouseout", function(e) {
    var badge = document.querySelector(".debugger-tooltip-badge");
    if (badge) badge.remove();
  });
</script>
"""


def _highlight_containers(tree: Any, container_selector: str, container_selector_type: str) -> None:  # noqa: ANN401
    """Highlight container nodes in tree matching selector."""
    try:
        engine = get_selector_engine(container_selector_type)
        containers = engine.select(tree, container_selector)
        for idx, container in enumerate(containers):
            if hasattr(container, "set"):
                container.set("data-debugger-container", "true")
                container.set("data-debugger-selector", container_selector)
                container.set("data-debugger-match-index", str(idx + 1))
    except Exception as err:  # noqa: BLE001
        logger.debug("Container highlighting skipped: %s", err)


def _highlight_fields(
    tree: Any,  # noqa: ANN401
    fields_config: dict[str, Any],
    default_sel_type: str,
) -> None:
    """Highlight field nodes in tree matching field selectors."""
    for field_name, field_cfg in fields_config.items():
        if not isinstance(field_cfg, dict):
            continue
        f_selector = field_cfg.get("selector")
        f_sel_type = field_cfg.get("selector_type", default_sel_type or "css")
        if not f_selector:
            continue

        try:
            engine = get_selector_engine(f_sel_type)
            field_nodes = engine.select(tree, f_selector)
            for f_node in field_nodes:
                if hasattr(f_node, "set"):
                    f_node.set("data-debugger-field", field_name)
                    f_node.set("data-debugger-field-selector", f_selector)
        except Exception as err:  # noqa: BLE001
            logger.debug("Field highlighting skipped for %s: %s", field_name, err)


def highlight_html_elements(
    html_content: str,
    container_selector: str | None = None,
    container_selector_type: str = "css",
    fields_config: dict[str, Any] | None = None,
) -> str:
    """Highlight container and field elements in HTML content for visual debugger preview."""
    if not html_content or not html_content.strip():
        return html_content

    try:
        tree = lxml.html.fromstring(html_content)
    except Exception:  # noqa: BLE001
        return html_content

    if container_selector:
        _highlight_containers(tree, container_selector, container_selector_type)

    if fields_config:
        _highlight_fields(tree, fields_config, container_selector_type)

    head_elem = tree.find("head")
    inject_frag = lxml.html.fragment_fromstring(f"<div>{INJECTED_PREVIEW_STYLES}</div>")

    if head_elem is not None:
        for child in list(inject_frag):
            head_elem.append(child)
    else:
        tree.append(inject_frag)

    try:
        return lxml.html.tostring(tree, encoding="unicode", method="html")
    except Exception:  # noqa: BLE001
        return html_content
