import os

class Settings:
    MEDUSA_URL = os.getenv('MEDUSA_URL', 'http://localhost:9000')
    MEDUSA_ADMIN_API_KEY = os.getenv('VIBECLOUD_API_KEY', os.getenv('MEDUSA_ADMIN_API_KEY', ''))

settings = Settings()
