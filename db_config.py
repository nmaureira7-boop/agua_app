import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_path = "/opt/render/project/src/wallet"

    print("Archivos en wallet:", os.listdir(wallet_path))

    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dsn="bluedate_tp",   # alias exacto del tnsnames.ora
        config_dir=wallet_path,
        wallet_location=wallet_path,
        wallet_password=os.getenv("WALLET_PASS")   # 👈 clave definida al descargar el wallet
    )
