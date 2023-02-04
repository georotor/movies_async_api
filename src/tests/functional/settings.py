from core.config import Settings


class TestSettings(Settings):
    service_url: str = 'http://0.0.0.0:8000'


test_settings = TestSettings()
