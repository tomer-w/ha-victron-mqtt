"""Token-based MQTT pairing with Victron GX devices."""

import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class PairingError(Exception):
    """Raised when token pairing with the GX device fails."""


@dataclass(frozen=True)
class PairingToken:
    """Credentials returned by a GX device after a successful pairing request."""

    token_name: str
    password: str


async def request_pairing_token(
    host: str,
    device_id: str,
    *,
    role: str = "homeassistant",
    session: aiohttp.ClientSession | None = None,
) -> PairingToken:
    """Request MQTT pairing credentials from a GX device via HTTPS.

    The GX device must have pairing mode enabled. On success the device
    returns credentials that grant exclusive MQTT broker access. If MQTT
    Access was turned off, it will change to "Paired devices only"
    automatically.

    Args:
        host: Hostname or IP of the GX device.
        device_id: Alphanumeric identifier for this client (e.g. installation_id).
        role: Role name sent to the GX device (default: "homeassistant").
        session: Optional aiohttp session to reuse. When *None* a temporary
            session is created and closed automatically.

    Returns:
        A PairingToken with token_name and password fields.

    Raises:
        ValueError: device_id contains non-alphanumeric characters.
        PairingError: The GX device rejected the pairing request.
        aiohttp.ClientError: Network-level failure.

    """
    if not device_id.isalnum():
        raise ValueError(f"device_id must be alphanumeric, got: {device_id!r}")

    if session is not None:
        return await _do_pairing_request(host, device_id, session, role=role)

    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False),
    ) as new_session:
        return await _do_pairing_request(host, device_id, new_session, role=role)


async def _do_pairing_request(
    host: str,
    device_id: str,
    session: aiohttp.ClientSession,
    *,
    role: str,
) -> PairingToken:
    url = f"https://{host}/auth/generate-token/"
    resp = await session.post(
        url,
        data={"role": role, "device_id": device_id},
    )
    if resp.status != 200:
        body = await resp.text()
        _LOGGER.error(
            "Token pairing request failed (HTTP %s): %s", resp.status, body
        )
        raise PairingError(f"HTTP {resp.status}: {body}")
    result: dict[str, Any] = await resp.json(content_type=None)
    _LOGGER.debug("Token pairing successful, token_name=%s", result.get("token_name"))
    return PairingToken(token_name=result["token_name"], password=result["password"])
