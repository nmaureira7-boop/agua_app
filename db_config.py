import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Logs de verificación
    print("DB_USER:", os.getenv("DB_USER"))
    print("DB_PASS definido:", os.getenv("DB_PASS") is not None)
    print("WALLET_PASS definido:", os.getenv("WALLET_PASS") is not None)

    wallet_path = "/opt/render/project/src/wallet"
    try:
        print("Archivos en wallet:", os.listdir(wallet_path))
    except Exception as e:
        print("Error al listar wallet:", e)

    # Conexión
    return oracledb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        dsn="bluedate_tp",   # alias exacto del tnsnames.ora
        config_dir=wallet_path,
        wallet_location=wallet_path,
        wallet_password=os.getenv("WALLET_PASS")
    )
