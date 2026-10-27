"""Exceptions raised by the Victron MQTT hub."""


class CannotConnectError(Exception):
    """Error to indicate we cannot connect."""


class AuthenticationError(CannotConnectError):
    """Authentication failed."""


class InvalidInstallationIdError(CannotConnectError):
    """The provided installation ID was not found on the broker."""


class NotConnectedError(Exception):
    """Error to indicate that we expected to be connected at this stage but is not."""


class PublishError(Exception):
    """Error to indicate that the MQTT client could not submit a message."""


class TopicNotFoundError(Exception):
    """Error to indicate that we expected to find a topic but it is not present."""
