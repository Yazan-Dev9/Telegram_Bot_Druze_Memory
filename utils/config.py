import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class BotConfig:
    def __init__(self):
        load_dotenv()

        self.BOT_TOKEN = os.getenv("BOT_TOKEN")
        self.ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
        self.FIRST_ADMIN_ID = os.getenv("FIRST_ADMIN_ID")
        self.DATABASE_NAME = os.getenv("DATABASE_NAME", "martyrs.db")
        self.UPLOAD_PATH = os.getenv("UPLOAD_PATH", "Upload")

        if not self.ADMIN_USER_ID:
            logger.warning(
                "ADMIN_USER_ID is not set in .env file. The bot will not be able to send admin notifications."
            )

        if self.ADMIN_USER_ID:
            try:
                self.ADMIN_USER_ID = int(self.ADMIN_USER_ID)
            except ValueError:
                logger.error("Invalid ADMIN_USER_ID in .env file.  Must be an integer.")
                self.ADMIN_USER_ID = None

        if self.FIRST_ADMIN_ID:
            try:
                self.FIRST_ADMIN_ID = int(self.FIRST_ADMIN_ID)
            except ValueError:
                logger.error(
                    "Invalid FIRST_ADMIN_ID in .env file.  Must be an integer."
                )
                self.FIRST_ADMIN_ID = None


config = BotConfig()
