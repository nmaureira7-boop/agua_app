import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_path = "/opt/render/project/src/wallet"
    try:
        return oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            dsn="bluedate_tp",
            config_dir=wallet_path,
            wallet_location=wallet_path,
            wallet_password=os.getenv("WALLET_PASS")
        )
    except Exception as e:
        print("Error al conectar a Oracle:", e)
        raise