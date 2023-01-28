from core.config import Settings


class TestSettings(Settings):
    service_url: str = 'http://api:8000'
    es_index: str = 'movies'
    es_id_field: str = 'id'


test_settings = TestSettings()
