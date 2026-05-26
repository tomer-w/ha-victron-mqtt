"""Test helpers for creating and managing mocked Hub instances for testing.

This module provides utilities for downstream projects that use victron_mqtt
to write their own tests involving Hub objects and MQTT message simulation.
"""

import asyncio
import json
import logging
from itertools import count
from typing import Any
from unittest.mock import MagicMock, patch

from paho.mqtt.client import ConnectFlags
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.reasoncodes import ReasonCode

from .._victron_enums import DeviceType
from ..constants import TOPIC_INSTALLATION_ID, OperationMode
from ..hub import Hub

logger = logging.getLogger(__name__)


async def create_mocked_hub(
    installation_id: str | None = None,
    operation_mode: OperationMode = OperationMode.FULL,
    device_type_exclude_filter: list[DeviceType] | None = None,
    update_frequency_seconds: int | None = None,
    disable_keepalive_loop: bool = True,
) -> Hub:
    """Create and return a mocked Hub object for testing.

    This function creates a Hub instance with a fully mocked MQTT client,
    allowing you to simulate MQTT messages and test Hub behavior without
    connecting to an actual MQTT broker.

    Args:
        installation_id: Optional Victron installation ID. If None, will be
            automatically set to "123" during connection.
        operation_mode: The operation mode for the Hub (FULL, READ_ONLY, or EXPERIMENTAL).
        device_type_exclude_filter: Optional list of device types to exclude from processing.
        update_frequency_seconds: Optional update frequency for metrics in seconds.
        disable_keepalive_loop: If True (default), disables the keepalive loop to prevent
            background tasks during testing. Set to False if you need to test keepalive behavior.

    Returns:
        A Hub instance with a mocked MQTT client, ready for testing.

    Example:
        ```python
        import pytest
        from victron_mqtt.testing import create_mocked_hub, inject_message, finalize_injection

        @pytest.mark.asyncio
        async def test_my_hub_integration():
            hub = await create_mocked_hub()
            await inject_message(hub, "N/123/battery/0/Soc", '{"value": 85}')
            await finalize_injection(hub)

            # Now test your code that uses the hub
            assert len(hub.devices) == 1
        ```
    """

    async def _async_noop(_self: Any) -> None:
        pass

    keepalive_patch: Any = patch.object(Hub, "_keepalive_loop", new=_async_noop) if disable_keepalive_loop else None

    if keepalive_patch:
        keepalive_patch.start()

    try:
        with patch("victron_mqtt.hub.mqtt.Client") as mock_client:
            hub = Hub(
                host="localhost",
                port=1883,
                username=None,
                password=None,
                use_ssl=False,
                installation_id=installation_id,
                operation_mode=operation_mode,
                device_type_exclude_filter=device_type_exclude_filter,
                update_frequency_seconds=update_frequency_seconds,
            )
            mocked_client = MagicMock()
            mock_client.return_value = mocked_client

            # Set up required mock methods
            mocked_client.subscribe = MagicMock()
            mocked_client.is_connected.return_value = True

            # Set the mocked client explicitly to prevent overwriting
            hub._client = mocked_client

            # Dynamically mock undefined attributes
            hub._process_device = MagicMock(name="_process_device")
            hub._process_metric = MagicMock(name="_process_metric")

            # Mock connect_async to trigger the _on_connect callback
            def mock_connect_async(*_args: Any, **_kwargs: Any) -> None:
                hub._on_connect(
                    hub._client, None, ConnectFlags(False), ReasonCode(PacketTypes.CONNACK, identifier=0), None
                )

            mocked_client.connect_async = MagicMock(name="connect_async", side_effect=mock_connect_async)

            # Ensure loop_start is a no-op
            mocked_client.loop_start = MagicMock(name="loop_start")

            # Mock on_message to handle incoming messages
            mocked_client.on_message = MagicMock(name="on_message")

            # Mock _subscribe to automatically publish a message to TOPIC_INSTALLATION_ID
            def mock_subscribe(topic: str):
                if topic == TOPIC_INSTALLATION_ID or topic == TOPIC_INSTALLATION_ID.replace("+", "123"):
                    mocked_client.on_message(
                        mocked_client, None, MagicMock(topic="N/123/system/0/Serial", payload=b'{"value": "123"}')
                    )
                    return
                assert "{installation_id}" not in topic
                assert not topic.startswith("N/+")

            mocked_client.subscribe = MagicMock(name="subscribe", side_effect=mock_subscribe)

            def parse_keepalive_options(json_string: str) -> str:
                """Parse the JSON string for keepalive options and return the echo value."""
                try:
                    options: dict[str, list[dict[str, str]]] = json.loads(json_string)
                    keepalive_options = options.get("keepalive-options", [])
                    if keepalive_options and isinstance(keepalive_options, list):
                        return keepalive_options[0].get("full-publish-completed-echo", "")
                    return ""
                except (json.JSONDecodeError, AttributeError, IndexError):
                    return ""

            def mock_publish(topic: str, value: str) -> None:
                if topic == "R/123/keepalive" and "suppress-republish" not in str(value):
                    echo = parse_keepalive_options(value)
                    keepalive_payload = json.dumps({"full-publish-completed-echo": echo, "value": 42})
                    logger.info("Sending mocked full_publish_completed")
                    mocked_client.on_message(
                        mocked_client,
                        None,
                        MagicMock(topic="N/123/full_publish_completed", payload=keepalive_payload.encode()),
                    )
                    logger.info("Mocked full_publish_completed")
                if topic.startswith("W/"):
                    read_topic = "N" + topic[1:]
                    mocked_client.on_message(mocked_client, None, MagicMock(topic=read_topic, payload=value.encode()))

            mocked_client.publish = MagicMock(name="publish", side_effect=mock_publish)

            await hub.connect()

            return hub
    finally:
        if keepalive_patch:
            keepalive_patch.stop()


async def sleep_short(mock_time: MagicMock | None = None):
    """Short async sleep to allow event loop to process callbacks.

    Args:
        mock_time: Optional MagicMock for time.monotonic() to advance time simulation.
    """
    if mock_time:
        times = count(0, 0.05)  # Start at 0, increment by 0.05 each call
        mock_time.side_effect = lambda: next(times)
    await asyncio.sleep(0.01)  # Allow event loop to process any scheduled callbacks
    if mock_time:
        mock_time.side_effect = None


async def hub_disconnect(hub: Hub, mock_time: MagicMock | None = None):
    """Disconnect a Hub instance gracefully.

    Args:
        hub: The Hub instance to disconnect.
        mock_time: Optional MagicMock for time.monotonic() to advance time simulation.
    """
    logger.info("calling hub.disconnect()")
    if mock_time:
        # As hub.disconnect is using asyncio.sleep(0.1), creating a sequence of increasing times
        times = count(0, 0.05)  # Start at 0, increment by 0.05 each call
        mock_time.side_effect = lambda: next(times)
    await hub.disconnect()
    if mock_time:
        mock_time.side_effect = None


async def inject_message(hub_instance: Hub, topic: str, payload: str, mock_time: MagicMock | None = None):
    """Inject a single MQTT message into a mocked Hub.

    This simulates receiving an MQTT message on the given topic with the
    specified payload. The Hub will process it as if it came from a real
    MQTT broker.

    Args:
        hub_instance: The Hub instance to inject the message into.
        topic: The MQTT topic string (e.g., "N/123/battery/0/Soc").
        payload: The JSON payload as a string (e.g., '{"value": 85}').
        mock_time: Optional MagicMock for time.monotonic() to advance time simulation.

    Example:
        ```python
        await inject_message(hub, "N/123/battery/0/Soc", '{"value": 85}')
        await inject_message(hub, "N/123/battery/0/Voltage", '{"value": 12.5}')
        ```
    """
    assert hub_instance._client is not None
    assert hub_instance._client.on_message is not None
    hub_instance._client.on_message(hub_instance._client, None, MagicMock(topic=topic, payload=payload.encode()))
    await sleep_short(mock_time)


async def finalize_injection(hub: Hub, disconnect: bool = True, mock_time: MagicMock | None = None):
    """Finalize the injection of messages into the Hub.

    This completes the message injection process by triggering keepalive,
    waiting for the first refresh to complete, and optionally disconnecting
    the Hub.

    Args:
        hub: The Hub instance to finalize.
        disconnect: Whether to disconnect the Hub after finalization. Default True.
        mock_time: Optional MagicMock for time.monotonic() to advance time simulation.

    Example:
        ```python
        hub = await create_mocked_hub()
        await inject_message(hub, "N/123/battery/0/Soc", '{"value": 85}')
        await finalize_injection(hub)

        # Hub is now ready for assertions
        assert hub.devices["battery_0"].get_metric("battery_soc").value == 85
        ```
    """
    # Wait for the connect task to finish
    logger.info("Sending keepalive to finalize injection")
    hub._keepalive(force=True)
    logger.info("Waiting for first refresh to complete")
    await hub.wait_for_first_refresh()
    # Allow the event loop to process any pending call_soon_threadsafe callbacks
    # (e.g., on_new_metric) that were scheduled during _handle_full_publish_message.
    await sleep_short(mock_time)
    logger.info("waiting completed")
    if disconnect:
        await hub_disconnect(hub, mock_time)
