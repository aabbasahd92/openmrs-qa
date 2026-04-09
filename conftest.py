import pytest

@pytest.fixture(scope="session")
def base_url():
    return "https://test3.openmrs.org/openmrs/spa"
