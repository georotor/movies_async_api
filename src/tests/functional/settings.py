from core.config import Settings


class TestSettings(Settings):
    service_url: str = 'http://api:8000'


test_settings = TestSettings()
