import os
from dotenv import load_dotenv
import oracledb

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SERVICE = os.getenv("DB_SERVICE")

def get_connection():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    return oracledb.connect(
        user=DB_USER,
        password=DB_PASS,
        dsn=dsn
    )