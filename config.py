import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    AGE_ADDRESS_FILL_LIMIT = int(os.getenv("AGE_ADDRESS_FILL_LIMIT", 10))
    ENRICHMENT_LIMIT = int(os.getenv("ENRICHMENT_LIMIT", 50))
    VERIPAGES_LIMIT = int(os.getenv("VERIPAGES_LIMIT", 20))
    EXPORT_LIMIT = int(os.getenv("EXPORT_LIMIT", 100))

    SPIDER_LIMIT = int(os.getenv("SPIDER_LIMIT", 1000))
    OVERALL_LIMIT = int(os.getenv("OVERALL_LIMIT", 200))
    
    
    
settings = Settings()