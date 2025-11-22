from dotenv import load_dotenv
import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    dsn = f"{DB_HOST}:{DB_PORT}/{DB_SERVICE}"
    return oracledb.connect(user=DB_USER, password=DB_PASS, dsn=dsn)