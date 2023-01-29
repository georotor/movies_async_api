from core.config import Settings


class TestSettings(Settings):
    service_url: str = 'http://0.0.0.0:8000'
    api_url: str = "/api/v1"


test_settings = TestSettings()
