import os
from pathlib import Path
from dotenv import load_dotenv

root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    SITE_URL: str = os.getenv("SITE_URL", "")
    ADMIN_IDS: list[int] = [
        int(admin_id.strip())
        for admin_id in os.getenv("ADMIN_IDS", "").split(",")
        if admin_id.strip()
    ]

settings = Settings()
