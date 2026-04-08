from __future__ import annotations

from typing import Any, Dict, List


SUPPORT_ANSWER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["answer", "needs_human", "citations"],
    "properties": {
        "answer": {"type": "string"},
        "needs_human": {"type": "boolean"},
        "citations": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}

RECOMMENDATION_ANSWER_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["answer", "recommendations"],
    "properties": {
        "answer": {"type": "string"},
        "recommendations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name"],
                "properties": {
                    "name": {"type": "string"},
                    "price_eur": {"type": ["number", "null"]},
                    "reason": {"type": ["string", "null"]},
                },
            },
        },
    },
}

ACTION_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["answer", "action_taken", "action_success"],
    "properties": {
        "answer": {"type": "string"},
        "action_taken": {"type": "string"},
        "action_success": {"type": "boolean"},
    },
}

SCHEMA_REGISTRY: Dict[str, Dict[str, Any]] = {
    "support_answer": SUPPORT_ANSWER_SCHEMA,
    "recommendation_answer": RECOMMENDATION_ANSWER_SCHEMA,
    "action_result": ACTION_RESULT_SCHEMA,
}


def get_schema(schema_name: str) -> Dict[str, Any] | None:
    return SCHEMA_REGISTRY.get(schema_name)


def validate_structured_output(payload: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if schema.get("type") != "object":
        return ["unsupported_schema_type"]

    if not isinstance(payload, dict):
        return ["payload_not_object"]

    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required:
        if field not in payload:
            errors.append(f"missing_required_field:{field}")

    for field, rules in properties.items():
        if field not in payload:
            continue

        value = payload[field]
        allowed_types = rules.get("type")

        if allowed_types is not None:
            if not _matches_type(value, allowed_types):
                errors.append(f"invalid_type:{field}")

        if allowed_types == "array" and "items" in rules:
            if isinstance(value, list):
                item_rules = rules["items"]
                for i, item in enumerate(value):
                    item_errors = _validate_item(item, item_rules)
                    for err in item_errors:
                        errors.append(f"{field}[{i}].{err}")

    return errors


def _validate_item(value: Any, rules: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    item_type = rules.get("type")

    if item_type and not _matches_type(value, item_type):
        errors.append("invalid_type")
        return errors

    if item_type == "object":
        required = rules.get("required", [])
        properties = rules.get("properties", {})

        if not isinstance(value, dict):
            errors.append("not_object")
            return errors

        for field in required:
            if field not in value:
                errors.append(f"missing_required_field:{field}")

        for field, field_rules in properties.items():
            if field not in value:
                continue
            if not _matches_type(value[field], field_rules.get("type")):
                errors.append(f"invalid_type:{field}")

    return errors


def _matches_type(value: Any, expected_type: Any) -> bool:
    if expected_type is None:
        return True

    if isinstance(expected_type, list):
        return any(_matches_type(value, t) for t in expected_type)

    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "null":
        return value is None

    return False