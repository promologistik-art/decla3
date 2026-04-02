import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DB_PATH = BASE_DIR / "tax_bot.db"

# Создаём директории
DOWNLOADS_DIR.mkdir(exist_ok=True)

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    
    # Налоговые ставки
    USN_RATE_INCOME = 6.0
    USN_RATE_INCOME_EXPENSE = 15.0
    MINIMAL_TAX_RATE = 1.0
    
    # Страховые взносы 2025
    INSURANCE_FIXED = 49500.0
    INSURANCE_PERCENT = 1.0
    INCOME_THRESHOLD = 300000.0
    
    # Лимиты
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    SESSION_TIMEOUT = 3600  # 1 hour

config = Config()