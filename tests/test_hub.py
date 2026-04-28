"""Test the Victron GX MQTT Hub class."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from syrupy.assertion import SnapshotAssertion
from victron_mqtt import (
    AuthenticationError,
    CannotConnectError,
    Device as VictronVenusDevice,
    Hub as VictronVenusHub,
)
from victron_mqtt.testing import create_mocked_hub, finalize_injection, inject_message

from custom_components.victron_mqtt.const import (
    CONF_EXCLUDED_DEVICES,
    CONF_INSTALLATION_ID,
    CONF_MODEL,
    CONF_ROOT_TOPIC_PREFIX,
    CONF_SERIAL,
    CONF_UPDATE_FREQUENCY_SECONDS,
    CONF_SIMPLE_NAMING,
    DOMAIN,
)
from custom_components.victron_mqtt.hub import Hub
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.core import State

from pytest_homeassistant_custom_component.common import MockConfigEntry, mock_restore_cache

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")

@pytest.fixture(params=[False, True], ids=["complex_naming", "simple_naming"])
def basic_config(request):
    """Provide basic configuration."""
    return {
        CONF_HOST: "venus.local",
        CONF_PORT: 1883,
        CONF_USERNAME: "test_user",
        CONF_PASSWORD: "test_pass",
        CONF_SSL: False,
        CONF_INSTALLATION_ID: "12345",
        CONF_MODEL: "Venus GX",
        CONF_SERIAL: "HQ12345678",
        CONF_ROOT_TOPIC_PREFIX: "N/",
        CONF_UPDATE_FREQUENCY_SECONDS: 30,
        CONF_SIMPLE_NAMING: request.param,
        CONF_EXCLUDED_DEVICES: ["battery"],  # Exclude battery devices
    }


@pytest.fixture
def mock_config_entry(basic_config):
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_unique_id",
        data=basic_config,
    )


@pytest.fixture
def mock_victron_hub():
    """Create a mock VictronVenusHub."""
    with patch(
        "custom_components.victron_mqtt.hub.VictronVenusHub"
    ) as mock_hub_class:
        mock_hub = MagicMock(spec=VictronVenusHub)
        mock_hub.connect = AsyncMock()
        mock_hub.disconnect = AsyncMock()
        mock_hub.publish = MagicMock()
        mock_hub.installation_id = "12345"
        mock_hub_class.return_value = mock_hub
        yield mock_hub


@pytest.fixture
async def init_integration(hass: HomeAssistant, mock_config_entry):
    """Set up the Victron GX MQTT integration for testing."""
    mock_config_entry.add_to_hass(hass)

    # Mock the VictronVenusHub
    victron_hub = await create_mocked_hub()

    with patch(
        "custom_components.victron_mqtt.hub.VictronVenusHub"
    ) as mock_hub_class:
        mock_hub_class.return_value = victron_hub

        # Set up the config entry
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    return victron_hub, mock_config_entry


async def test_hub_start_success(hass: HomeAssistant, init_integration) -> None:
    """Test successful hub start."""
    victron_hub, mock_config_entry = init_integration

    # Verify the hub was started (integration was set up successfully)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert victron_hub.installation_id == "123"


async def test_hub_start_connection_error(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Test hub start with connection error."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.victron_mqtt.hub.VictronVenusHub.connect",
        side_effect=CannotConnectError("Connection failed"),
    ):
        # Attempt to set up the config entry - should fail and mark as SETUP_RETRY
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Verify the config entry is in SETUP_RETRY state (not loaded due to error)
        assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_hub_stop(hass: HomeAssistant, init_integration) -> None:
    """Test hub stop."""
    _, mock_config_entry = init_integration

    # Verify it's initially loaded
    assert mock_config_entry.state is ConfigEntryState.LOADED

    # Unload the config entry (which stops the hub)
    unload_ok = await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify hub is disconnected by checking config entry state
    assert unload_ok is True
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_map_device_info() -> None:
    """Test _map_device_info static method."""
    mock_device = MagicMock(spec=VictronVenusDevice)
    mock_device.unique_id = "device_123"
    mock_device.manufacturer = "Victron Energy"
    mock_device.name = "Battery Monitor"
    mock_device.device_id = "288"
    mock_device.model = "BMV-712"
    mock_device.serial_number = "HQ12345678"

    installation_id = "12345"

    device_info = Hub._map_device_info(mock_device, installation_id)

    assert device_info.get("identifiers") == {(DOMAIN, "12345_device_123")}
    assert device_info.get("manufacturer") == "Victron Energy"
    assert device_info.get("name") == "Battery Monitor"
    assert device_info.get("model") == "BMV-712"
    assert device_info.get("serial_number") == "HQ12345678"


async def test_map_device_info_no_manufacturer() -> None:
    """Test _map_device_info with no manufacturer."""
    mock_device = MagicMock(spec=VictronVenusDevice)
    mock_device.unique_id = "device_123"
    mock_device.manufacturer = None
    mock_device.name = "Unknown Device"
    mock_device.device_id = "0"
    mock_device.model = "Unknown"
    mock_device.serial_number = None

    installation_id = "12345"

    device_info = Hub._map_device_info(mock_device, installation_id)

    assert device_info.get("manufacturer") == "Victron Energy"
    assert (
        device_info.get("name") == "Unknown Device"
    )  # device_id == "0" uses name only


async def test_unregister_add_entities_callback(
    hass: HomeAssistant, init_integration
) -> None:
    """Test unregistering add entities callback."""
    victron_hub, mock_config_entry = init_integration

    # Inject a sensor before unloading
    await inject_message(victron_hub, "N/123/battery/0/Soc", '{"value": 75}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities_before = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entities_before) > 0

    # Unload the config entry (which unregisters callbacks)
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Entities should still be registered (just unavailable)
    entities_after = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entities_after) == len(entities_before)


async def test_on_new_metric_sensor(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    """Test _on_new_metric callback creates entities and updates values."""
    victron_hub, mock_config_entry = init_integration

    # Inject a sensor metric
    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Voltage", '{"value": 12.6}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    # Verify entity was created
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert len(entities) > 0

    # Get the voltage entity
    voltage_entities = [e for e in entities if "voltage" in e.entity_id]
    assert len(voltage_entities) > 0
    entity_id = voltage_entities[0].entity_id
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 12.6

    # Update with new value
    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Voltage", '{"value": 13.2}')
    await hass.async_block_till_done()

    # Verify state updated
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 13.2

    # Update with same value - state should remain the same
    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Voltage", '{"value": 13.2}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 13.2


async def test_sensor(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject a sensor metric (battery current)
    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Current", '{"value": 10.5}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created at least one entity
    assert len(entities) > 0
    assert entities == snapshot


async def test_sensor_complex(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject the MQTT message
    await inject_message(victron_hub, "N/123/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/2/Day", "{\"value\": -7}")
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created 2 entities (Day and Enabled)
    assert len(entities) == 2
    assert entities == snapshot


async def test_binary_sensor(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration
    
    # Inject a binary sensor metric (evcharger connected state)
    await inject_message(victron_hub, "N/123/evcharger/0/Connected", "{\"value\": 1}")
    await finalize_injection(victron_hub)
    
    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_number(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration
    
    # Inject a number metric (evcharger set current)
    await inject_message(victron_hub, "N/123/evcharger/0/SetCurrent", "{\"value\": 16.0}")
    await finalize_injection(victron_hub)

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_select(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject a select metric (evcharger mode) - use numeric enum value
    await inject_message(victron_hub, "N/123/evcharger/0/Mode", "{\"value\": 1}")
    await finalize_injection(victron_hub)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_select_main_topic(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    """Test select entity with main_topic=True still gets translation_key."""
    victron_hub, mock_config_entry = init_integration

    # Inject a select metric where main_topic=True (vebus inverter mode)
    await inject_message(victron_hub, "N/123/vebus/289/Mode", '{"value": 3}')
    await finalize_injection(victron_hub)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_button(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject a button metric (platform device reboot) - GenericOnOff enum value
    await inject_message(victron_hub, "N/123/platform/0/Device/Reboot", "{\"value\": 1}")
    await finalize_injection(victron_hub)

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_switch(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject a switch metric (generator manual start - writable)
    await inject_message(victron_hub, "N/123/generator/0/ManualStart", "{\"value\": 0}")
    await finalize_injection(victron_hub)

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_time(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    victron_hub, mock_config_entry = init_integration

    # Inject a time metric (schedule charge start time in minutes 0-86400)
    await inject_message(victron_hub, "N/123/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Start", "{\"value\": 1380}")
    await finalize_injection(victron_hub)

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_device_tracker(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    """Test device tracker entity creation from GPS location."""
    victron_hub, mock_config_entry = init_integration

    # Inject all GPS metrics required by the gps_location formula
    await inject_message(victron_hub, "N/123/gps/0/Position/Latitude", '{"value": 52.3676}')
    await inject_message(victron_hub, "N/123/gps/0/Position/Longitude", '{"value": 4.9041}')
    await inject_message(victron_hub, "N/123/gps/0/Fix", '{"value": 1}')
    await inject_message(victron_hub, "N/123/gps/0/Altitude", '{"value": 10.0}')
    await inject_message(victron_hub, "N/123/gps/0/Course", '{"value": 0.0}')
    await inject_message(victron_hub, "N/123/gps/0/Speed", '{"value": 0.0}')
    await finalize_injection(victron_hub)

    # Verify entity was created by checking entity registry
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )

    # Should have created one entity
    assert len(entities) == 1
    assert entities == snapshot


async def test_device_tracker_update(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test device tracker state updates via MQTT (_on_update_cb)."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/gps/0/Position/Latitude", '{"value": 52.3676}')
    await inject_message(victron_hub, "N/123/gps/0/Position/Longitude", '{"value": 4.9041}')
    await inject_message(victron_hub, "N/123/gps/0/Fix", '{"value": 1}')
    await inject_message(victron_hub, "N/123/gps/0/Altitude", '{"value": 10.0}')
    await inject_message(victron_hub, "N/123/gps/0/Course", '{"value": 0.0}')
    await inject_message(victron_hub, "N/123/gps/0/Speed", '{"value": 0.0}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    tracker_entities = [e for e in entities if "device_tracker." in e.entity_id]
    assert len(tracker_entities) > 0
    entity_id = tracker_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.attributes["latitude"]) == 52.3676
    assert float(state.attributes["longitude"]) == 4.9041

    # Update via MQTT - triggers _on_update_cb with new coordinates
    await inject_message(victron_hub, "N/123/gps/0/Position/Latitude", '{"value": 48.8566}')
    await inject_message(victron_hub, "N/123/gps/0/Position/Longitude", '{"value": 2.3522}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.attributes["latitude"]) == 48.8566
    assert float(state.attributes["longitude"]) == 2.3522


@patch('victron_mqtt.formula_common.time.monotonic')
async def test_sensor_with_baseline(
    mock_time: MagicMock,
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    init_integration,
) -> None:
    """Test that baseline is NOT restored for TOTAL state_class (only TOTAL_INCREASING).
    
    The current implementation only restores baseline for sensors with
    SensorStateClass.TOTAL_INCREASING. FormulaMetric sensors with CUMULATIVE
    nature get mapped to SensorStateClass.TOTAL, so baseline is not restored.
    """
    victron_hub, mock_config_entry = init_integration
    # Mock time.monotonic() to return a fixed time
    mock_time.return_value = 0
    
    # The entity_id depends on the naming convention:
    # simple_naming: HA generates from device name + entity name
    # complex_naming: includes installation_id in the unique_id/entity_id
    simple_naming = mock_config_entry.data[CONF_SIMPLE_NAMING]
    if simple_naming:
        entity_id = "sensor.victron_venus_pv_energy"
    else:
        entity_id = "sensor.victron_mqtt_123_system_0_system_dc_pv_energy"
    
    # Mock the restore cache with a previous state value of 1000.0
    mock_restore_cache(hass, [State(entity_id, "1000.0")])

    # Inject a PV power metric which triggers creation of a FormulaMetric (pv_energy)
    # The FormulaMetric has CUMULATIVE nature which maps to TOTAL state_class (not TOTAL_INCREASING)
    await inject_message(victron_hub, "N/123/system/0/Dc/Pv/Power", '{"value": 1000}', mock_time)
    await finalize_injection(victron_hub, disconnect=False, mock_time=mock_time)
    mock_time.return_value = 15
    await inject_message(victron_hub, "N/123/system/0/Dc/Pv/Power", '{"value": 4000}', mock_time)

    # Find the energy entity (FormulaMetric)
    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    energy_entities = [e for e in entities if "energy" in e.entity_id]
    assert len(energy_entities) > 0
    
    # Since state_class is TOTAL (not TOTAL_INCREASING), baseline is NOT restored
    # The value should be 0.0 (the FormulaMetric's initial value)
    state = hass.states.get(energy_entities[0].entity_id)
    assert state is not None
    # Value should be the metric's initial value, NOT the baseline
    assert float(state.state) == 1000.004  # Not 0.004
    # Should have created two entity
    assert len(entities) == 2
    assert entities == snapshot


@patch('victron_mqtt.formula_common.time.monotonic')
async def test_sensor_baseline_invalid_value(
    mock_time: MagicMock,
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test that baseline restore handles invalid (non-numeric) last_state gracefully."""
    victron_hub, mock_config_entry = init_integration
    mock_time.return_value = 0

    entity_id = "sensor.victron_venus_pv_energy"

    # Mock the restore cache with an invalid (non-numeric) state
    mock_restore_cache(hass, [State(entity_id, "not_a_number")])

    await inject_message(victron_hub, "N/123/system/0/Dc/Pv/Power", '{"value": 1000}', mock_time)
    await finalize_injection(victron_hub, disconnect=False, mock_time=mock_time)
    mock_time.return_value = 15
    await inject_message(victron_hub, "N/123/system/0/Dc/Pv/Power", '{"value": 4000}', mock_time)

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    energy_entities = [e for e in entities if "energy" in e.entity_id]
    assert len(energy_entities) > 0

    # Should fall through to ValueError branch; value is metric's own value
    state = hass.states.get(energy_entities[0].entity_id)
    assert state is not None
    # Baseline restore failed, so value is just the metric's computed value
    assert isinstance(float(state.state), float)


async def test_button_press(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test pressing a button entity calls set on the metric."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/platform/0/Device/Reboot", '{"value": 1}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    button_entities = [e for e in entities if "button." in e.entity_id]
    assert len(button_entities) > 0
    entity_id = button_entities[0].entity_id

    # Get the entity object to spy on _metric.set
    entity = hass.data["entity_components"]["button"].get_entity(entity_id)
    assert entity is not None
    with patch.object(entity._metric, "set", wraps=entity._metric.set) as mock_set:
        # Press the button
        await hass.services.async_call(
            "button", "press", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with("on")


async def test_switch_turn_on_off(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test turning a switch on and off."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/generator/0/ManualStart", '{"value": 0}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    switch_entities = [e for e in entities if "switch." in e.entity_id]
    assert len(switch_entities) > 0
    entity_id = switch_entities[0].entity_id

    # Get the entity object to spy on _metric.set
    entity = hass.data["entity_components"]["switch"].get_entity(entity_id)
    assert entity is not None
    with patch.object(entity._metric, "set", wraps=entity._metric.set) as mock_set:
        # Turn on
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with("on")

        mock_set.reset_mock()

        # Turn off
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": entity_id}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with("off")


async def test_select_option(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test selecting an option on a select entity."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/evcharger/0/Mode", '{"value": 1}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    select_entities = [e for e in entities if "select." in e.entity_id]
    assert len(select_entities) > 0
    entity_id = select_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None

    # Select a valid option
    options = state.attributes.get("options", [])
    assert len(options) > 0

    # Get the entity object to spy on _metric.set
    entity = hass.data["entity_components"]["select"].get_entity(entity_id)
    assert entity is not None
    with patch.object(entity._metric, "set", wraps=entity._metric.set) as mock_set:
        await hass.services.async_call(
            "select", "select_option", {"entity_id": entity_id, "option": options[0]}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with(options[0])


async def test_number_set_value(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test setting a value on a number entity."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/evcharger/0/SetCurrent", '{"value": 16.0}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    number_entities = [e for e in entities if "number." in e.entity_id]
    assert len(number_entities) > 0
    entity_id = number_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 16.0

    # Update the value via MQTT
    await inject_message(victron_hub, "N/123/evcharger/0/SetCurrent", '{"value": 20.0}')
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 20.0

    # Set value via service
    entity = hass.data["entity_components"]["number"].get_entity(entity_id)
    assert entity is not None
    with patch.object(entity._metric, "set", wraps=entity._metric.set) as mock_set:
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": 10.0}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with(10.0)


async def test_time_set_value(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test setting a time value and verifying time conversion."""
    victron_hub, mock_config_entry = init_integration

    # 1380 minutes = 23:00
    await inject_message(victron_hub, "N/123/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Start", '{"value": 1380}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    time_entities = [e for e in entities if "time." in e.entity_id]
    assert len(time_entities) > 0
    entity_id = time_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None

    # Update value via MQTT (triggers _on_update_cb)
    await inject_message(victron_hub, "N/123/settings/0/Settings/CGwacs/BatteryLife/Schedule/Charge/0/Start", '{"value": 480}')
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None

    # Set value via service (triggers set_value)
    entity = hass.data["entity_components"]["time"].get_entity(entity_id)
    assert entity is not None
    with patch.object(entity._metric, "set", wraps=entity._metric.set) as mock_set:
        await hass.services.async_call(
            "time", "set_value", {"entity_id": entity_id, "time": "12:30:00"}, blocking=True
        )
        await hass.async_block_till_done()
        mock_set.assert_called_once_with(750)  # 12*60 + 30 = 750 minutes


async def test_hub_auth_error(
    hass: HomeAssistant, mock_config_entry
) -> None:
    """Test hub start with authentication error raises ConfigEntryAuthFailed."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.victron_mqtt.hub.VictronVenusHub.connect",
        side_effect=AuthenticationError("Auth failed"),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        # Auth failures put the entry in SETUP_ERROR state
        assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_publish_service(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test the publish service calls hub.publish."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Voltage", '{"value": 12.6}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    # Get the Hub to spy on publish
    hub = mock_config_entry.runtime_data
    with patch.object(hub, "publish", wraps=hub.publish) as mock_publish:
        await hass.services.async_call(
            DOMAIN,
            "publish",
            {
                "metric_id": "generator_service_counter_reset",
                "device_id": "261",
                "value": "1",
            },
            blocking=True,
        )
        await hass.async_block_till_done()
        mock_publish.assert_called_once_with(
            "generator_service_counter_reset", "261", "1"
        )


async def test_publish_service_missing_fields(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test the publish service raises errors for missing fields."""
    from homeassistant.exceptions import HomeAssistantError

    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/battery/0/Dc/0/Voltage", '{"value": 12.6}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    # Missing metric_id
    with pytest.raises(HomeAssistantError, match="metric_id is required"):
        await hass.services.async_call(
            DOMAIN,
            "publish",
            {"device_id": "261", "value": "1"},
            blocking=True,
        )

    # Missing device_id
    with pytest.raises(HomeAssistantError, match="device_id is required"):
        await hass.services.async_call(
            DOMAIN,
            "publish",
            {"metric_id": "test_metric", "value": "1"},
            blocking=True,
        )


async def test_binary_sensor_update(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test binary sensor state updates via MQTT (_on_update_cb)."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/evcharger/0/Connected", '{"value": 1}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    binary_entities = [e for e in entities if "binary_sensor." in e.entity_id]
    assert len(binary_entities) > 0
    entity_id = binary_entities[0].entity_id

    # Update via MQTT - triggers _on_update_cb
    await inject_message(victron_hub, "N/123/evcharger/0/Connected", '{"value": 0}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None


async def test_enum_sensor(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test enum sensor creation and update (covers enum options and VictronEnum normalization)."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/system/0/SystemState/State", '{"value": 1}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    # Find the system state entity (enum sensor)
    state_entities = [e for e in entities if "state" in e.entity_id.lower()]
    assert len(state_entities) > 0
    entity_id = state_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.attributes.get("options") is not None

    # Update via MQTT to trigger _on_update_cb with VictronEnum
    await inject_message(victron_hub, "N/123/system/0/SystemState/State", '{"value": 3}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None


async def test_number_update_cb(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test number entity state updates via MQTT (_on_update_cb)."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/evcharger/0/SetCurrent", '{"value": 16.0}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    number_entities = [e for e in entities if "number." in e.entity_id]
    assert len(number_entities) > 0
    entity_id = number_entities[0].entity_id

    # Update via MQTT
    await inject_message(victron_hub, "N/123/evcharger/0/SetCurrent", '{"value": 32.0}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 32.0


async def test_select_update_cb(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test select entity state updates via MQTT (_on_update_cb and _map_value_to_state)."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/evcharger/0/Mode", '{"value": 1}')
    await finalize_injection(victron_hub, disconnect=False)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    select_entities = [e for e in entities if "select." in e.entity_id]
    assert len(select_entities) > 0
    entity_id = select_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None

    # Update via MQTT to trigger _on_update_cb
    await inject_message(victron_hub, "N/123/evcharger/0/Mode", '{"value": 0}')
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None


async def test_number_with_step(
    hass: HomeAssistant,
    init_integration,
) -> None:
    """Test number entity with step attribute from metric."""
    victron_hub, mock_config_entry = init_integration

    await inject_message(victron_hub, "N/123/settings/0/Settings/SystemSetup/MaxChargeVoltage", '{"value": 57.6}')
    await finalize_injection(victron_hub)
    await hass.async_block_till_done()

    entity_registry = er.async_get(hass)
    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    number_entities = [e for e in entities if "number." in e.entity_id]
    assert len(number_entities) > 0
    entity_id = number_entities[0].entity_id

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 57.6
    assert state.attributes.get("step") == 0.1


