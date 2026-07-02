import ast
from pathlib import Path


def _is_topic_descriptor_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "TopicDescriptor"


def _is_string_constant_keyword(keyword: ast.keyword) -> bool:
    return keyword.arg is not None and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str)


def test_vebus_hub4_disable_charge_uses_existing_ess_switch_id() -> None:
    victron_topics_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components/victron_mqtt/_vendor/victron_mqtt/_victron_topics.py"
    )
    module = ast.parse(victron_topics_path.read_text(encoding="utf-8"))

    matching_descriptors = []
    for node in ast.walk(module):
        if not _is_topic_descriptor_call(node):
            continue

        keyword_values = {
            keyword.arg: keyword.value.value
            for keyword in node.keywords
            if _is_string_constant_keyword(keyword)
        }
        if keyword_values.get("topic") == "N/{installation_id}/vebus/{device_id}/Hub4/DisableCharge":
            matching_descriptors.append(keyword_values)

    assert len(matching_descriptors) == 1
    assert matching_descriptors[0]["short_id"] == "multi_disable_charge"
