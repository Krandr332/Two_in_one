import os
from dotenv import load_dotenv

load_dotenv()

class ENV:
    DATABASE_URL = os.getenv("DATABASE_URL_SHORT_URL")
