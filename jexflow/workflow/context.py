from typing import Any


class ExecutionContext:
    """Manages variable state, step results, and loop stack during execution."""

    def __init__(self, variables: dict[str, Any] | None = None) -> "ExecutionContext":
        """Init.

        Args:
        variables: A dictionary of global variables.
        """
        self.global_variables: dict[str, Any] = variables or {}
        self.step_results: dict[str, list[dict[str, Any]]] = {}
        self._loop_stack: list[dict[str, Any]] = []

    def set_step_result(self, step_id: str, results: list[dict[str, Any]]) -> None:
        """Set the results of a step."""
        self.step_results[step_id] = results

    def get_step_result(self, step_id: str) -> list[dict[str, Any]]:
        """Return the results of a step."""
        return self.step_results.get(step_id, [])

    def push_loop_context(self, context: dict[str, Any]) -> None:
        """Pushes a new loop context onto the stack."""
        self._loop_stack.append(context)

    def pop_loop_context(self) -> None:
        """Pops the innermost loop context from the stack."""
        if self._loop_stack:
            self._loop_stack.pop()

    def get_template_context(self) -> dict[str, Any]:
        """Build combined variable dictionary for template rendering.

        Precedence (lowest to highest):
        1. Global variables
        2. Step results by step_id
        3. Active loop context stack (outermost to innermost).
        """
        ctx = dict(self.global_variables) | self.step_results
        for frame in self._loop_stack:
            ctx |= frame

        return ctx
