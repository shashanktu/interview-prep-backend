
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
# print(DB_URL)
CONTAINER_SAS_URL = os.getenv("CONTAINER_SAS_URL")

class ai_config:
    endpoint=os.getenv("AI_ENDPOINT")
    deployment=os.getenv("AI_MODEL")
    subscription_key=os.getenv("AI_CONTENT_KEY")
    api_version=os.getenv("AI_CONTENT_VERSION")