import os

# Telegram Bot Token (Termux में set होगा)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# PostgreSQL Database URL (Render environment में set होगा)
DATABASE_URL = os.getenv("DATABASE_URL")

# Main Admins (comma separated IDs in env)
MAIN_ADMINS = [
    int(admin_id)
    for admin_id in os.getenv("MAIN_ADMINS", "").split(",")
    if admin_id.strip()
]

# Basic safety check
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")
