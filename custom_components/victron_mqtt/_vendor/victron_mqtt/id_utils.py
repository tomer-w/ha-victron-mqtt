"""Utility functions for ID manipulation."""
import re
from collections.abc import Callable


# Complex is: "Switch {output:switch_{output}_custom_name} Dimming"
def replace_complex_ids(orig_str: str, match_func: Callable[[re.Match[str]], str]) -> str:
    """Replace placeholders in the string with matched items from self.key_values."""

    # Match {key:name_with_nested_{placeholder}} in the string
    pattern = re.compile(r"\{(?P<moniker>[^:]+:(?:[^{}]|{[^{}]*})+)\}")
    return pattern.sub(match_func, orig_str)

# Complex is: "Switch {output:switch_{output}_custom_name} Dimming"
# Simple is: "Switch {output} Dimming"
def replace_complex_id_to_simple(orig_str: str) -> str:
    """Replace complex placeholders in the string with simple ones."""
    def replace_match(match: re.Match[str]) -> str:
        moniker = match.group('moniker')
        key, suffix = moniker.split(':', 1)
        assert key, f"Invalid moniker format: {moniker} in topic: {orig_str}"
        assert suffix, f"Invalid moniker format: {moniker} in topic: {orig_str}"
        return f"{{{key}}}"

    return replace_complex_ids(orig_str, replace_match)


def reraise_same_exception(exc: Exception) -> None:
    """Reraise the same exception, preserving the traceback."""
    new = type(exc)(*exc.args)
    new.__dict__.update(exc.__dict__)
    raise new from exc
