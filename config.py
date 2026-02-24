import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./license.db")

MAIN_ADMINS = ["1086634832"]
