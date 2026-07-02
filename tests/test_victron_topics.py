from pathlib import Path


def test_vebus_hub4_disable_charge_uses_existing_ess_switch_id() -> None:
    victron_topics = Path(
        "custom_components/victron_mqtt/_vendor/victron_mqtt/_victron_topics.py"
    ).read_text(encoding="utf-8")

    assert (
        'topic="N/{installation_id}/vebus/{device_id}/Hub4/DisableCharge",\n'
        '        message_type=MetricKind.SWITCH,\n'
        '        short_id="multi_disable_charge",'
    ) in victron_topics
