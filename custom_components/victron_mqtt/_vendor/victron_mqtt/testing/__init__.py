"""Testing utilities for victron_mqtt.

This module provides helper functions and utilities for testing code that
uses the victron_mqtt library. Downstream projects can import these utilities
to write their own tests involving Hub objects and MQTT message simulation.

Example:
    ```python
    from victron_mqtt.testing import create_mocked_hub, inject_message, finalize_injection

    async def test_my_integration():
        hub = await create_mocked_hub()
        await inject_message(hub, "N/123/battery/0/Soc", '{"value": 85}')
        await finalize_injection(hub)

        # Your test assertions here
        assert len(hub.devices) == 1
    ```
"""

from .hub_helpers import (
    create_mocked_hub,
    finalize_injection,
    hub_disconnect,
    inject_message,
    sleep_short,
)

__all__ = [
    "create_mocked_hub",
    "finalize_injection",
    "hub_disconnect",
    "inject_message",
    "sleep_short",
]
