"""Global fixtures for Fing integration tests."""
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield

@pytest.fixture(autouse=True)
def prevent_socket_connections(socket_enabled):
    """Prevent socket connections during tests."""
    return
