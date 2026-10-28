import pytest

from company_brain.store import load_vec_extension


class NoExtensionConnection:
    """Stands in for sqlite3 builds compiled without loadable-extension support
    (e.g. the python.org macOS installer), where the method does not exist."""


def test_missing_extension_support_explains_fix():
    with pytest.raises(RuntimeError, match="enable_load_extension.*Homebrew|uv"):
        load_vec_extension(NoExtensionConnection())
