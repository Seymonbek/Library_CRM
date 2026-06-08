"""
Bot konfiguratsiyasi.

Barcha sozlamalar .env faylidan o'qiladi.
API_BASE_URL — Django API manzili (bot shu orqali gaplashadi).
BOT_TOKEN — Telegram BotFather'dan olingan token.
"""

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
