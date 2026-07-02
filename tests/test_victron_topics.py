import ast
from pathlib import Path


def test_vebus_hub4_disable_charge_uses_existing_ess_switch_id() -> None:
    victron_topics_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components/victron_mqtt/_vendor/victron_mqtt/_victron_topics.py"
    )
    module = ast.parse(victron_topics_path.read_text(encoding="utf-8"))

    matching_descriptors = []
    for node in ast.walk(module):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name) or node.func.id != "TopicDescriptor":
            continue

        keyword_values = {
            keyword.arg: keyword.value.value
            for keyword in node.keywords
            if keyword.arg is not None and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str)
        }
        if keyword_values.get("topic") == "N/{installation_id}/vebus/{device_id}/Hub4/DisableCharge":
            matching_descriptors.append(keyword_values)

    assert len(matching_descriptors) == 1
    assert matching_descriptors[0]["short_id"] == "multi_disable_charge"
