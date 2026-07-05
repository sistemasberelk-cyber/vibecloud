import os

class Settings:
    MEDUSA_URL = os.getenv('MEDUSA_URL', 'http://localhost:9000')
    MEDUSA_ADMIN_API_KEY = os.getenv('VIBECLOUD_API_KEY', os.getenv('MEDUSA_ADMIN_API_KEY', ''))
    
    MEDUSA_B2B_DISCOUNT_PERCENT = float(os.getenv('MEDUSA_B2B_DISCOUNT_PERCENT', '0.30'))
    MEDUSA_SYNC_BATCH_SIZE = int(os.getenv('MEDUSA_SYNC_BATCH_SIZE', '50'))
    STOREFRONT_URL = os.getenv('STOREFRONT_URL', 'http://localhost:3000')

settings = Settings()
