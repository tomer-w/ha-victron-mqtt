"""Test file format validation to prevent Windows line endings and BOM issues."""

from pathlib import Path

import pytest


CUSTOM_COMPONENTS_DIR = Path(__file__).parent.parent / "custom_components" / "victron_mqtt"


def get_shell_scripts() -> list[Path]:
    """Get all shell script files in the custom_components directory."""
    return list(CUSTOM_COMPONENTS_DIR.glob("**/*.sh"))


@pytest.mark.parametrize("script_path", get_shell_scripts(), ids=lambda p: p.name)
def test_shell_scripts_have_unix_line_endings(script_path: Path) -> None:
    """Verify shell scripts use Unix line endings (LF) not Windows (CRLF)."""
    content = script_path.read_bytes()
    
    # Check for CRLF (Windows line endings)
    assert b"\r\n" not in content, (
        f"{script_path.name} has Windows line endings (CRLF). "
        "Run: sed -i 's/\\r$//' " + str(script_path)
    )


@pytest.mark.parametrize("script_path", get_shell_scripts(), ids=lambda p: p.name)
def test_shell_scripts_have_no_bom(script_path: Path) -> None:
    """Verify shell scripts don't have UTF-8 BOM which breaks bash."""
    content = script_path.read_bytes()
    
    # UTF-8 BOM bytes
    utf8_bom = b"\xef\xbb\xbf"
    assert not content.startswith(utf8_bom), (
        f"{script_path.name} has UTF-8 BOM which breaks bash execution. "
        "Run: sed -i '1s/^\\xEF\\xBB\\xBF//' " + str(script_path)
    )
