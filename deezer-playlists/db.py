import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        user=os.getenv("DB_USER", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "deezer_app"),
        password=os.getenv("DB_PASSWORD", "TU_PASSWORD"),
        port=os.getenv("DB_PORT", 5432)
    )