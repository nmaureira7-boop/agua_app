from dotenv import load_dotenv
import os
import oracledb

# Cargar variables desde el archivo .env
load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_SERVICE = os.getenv("DB_SERVICE")

import oracledb
import os

def get_connection():
    dsn = f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_SERVICE')}"
    return oracledb.connect(
        user=os.getenv("nmaureira7@gmail.com"),
        password=os.getenv("Nicoxx164325."),
        dsn=dsn
    )
