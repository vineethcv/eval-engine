from __future__ import annotations

from typing import Any, Dict, List


class ToolSimulator:
    def __init__(self, tool_scenarios: Dict[str, Any] | None = None):
        self.tool_scenarios = tool_scenarios or {}

    def run(self, tool_name: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        if tool_name not in self.tool_scenarios:
            return {
                "error": f"Unknown tool: {tool_name}",
                "success": False,
            }

        tool_data = self.tool_scenarios[tool_name]

        # Simple key-based lookup (order_id, etc.)
        key = list(input_payload.values())[0] if input_payload else None

        if key in tool_data:
            return {
                "success": True,
                "data": tool_data[key],
            }

        return {
            "success": False,
            "error": f"No data found for input: {input_payload}",
        }


def simulate_tool_sequence(
    simulator: ToolSimulator,
    steps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    trace = []

    for step in steps:
        tool = step["tool"]
        input_payload = step.get("input", {})

        output = simulator.run(tool, input_payload)

        trace.append(
            {
                "tool": tool,
                "input": input_payload,
                "output": output,
            }
        )

    return trace