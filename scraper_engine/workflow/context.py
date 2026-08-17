from typing import Dict, Any, List, Optional


class ExecutionContext:
    """Manages variable state, step results, and loop stack during execution."""

    def __init__(self, variables: Optional[Dict[str, Any]] = None):
        self.global_variables: Dict[str, Any] = variables or {}
        self.step_results: Dict[str, List[Dict[str, Any]]] = {}
        self._loop_stack: List[Dict[str, Any]] = []

    def set_step_result(self, step_id: str, results: List[Dict[str, Any]]) -> None:
        self.step_results[step_id] = results

    def get_step_result(self, step_id: str) -> List[Dict[str, Any]]:
        return self.step_results.get(step_id, [])

    def push_loop_context(self, context: Dict[str, Any]) -> None:
        self._loop_stack.append(context)

    def pop_loop_context(self) -> None:
        if self._loop_stack:
            self._loop_stack.pop()

    def get_template_context(self) -> Dict[str, Any]:
        """
        Builds combined variable dictionary for template rendering.
        Precedence (lowest to highest):
        1. Global variables
        2. Step results by step_id
        3. Active loop context stack (outermost to innermost)
        """
        ctx: Dict[str, Any] = dict(self.global_variables)
        for step_id, res in self.step_results.items():
            ctx[step_id] = res

        for frame in self._loop_stack:
            ctx.update(frame)

        return ctx
