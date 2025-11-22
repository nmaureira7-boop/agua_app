import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

wallet_path = "/opt/render/project/src/wallet"

# Inicializar el cliente Oracle SOLO una vez
oracledb.init_oracle_client(config_dir=wallet_path)

def get_connection():
    try:
        return oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            dsn="bluedate_tp"  # Debe coincidir EXACTO con tu tnsnames.ora
        )
    except Exception as e:
        print("Error al conectar a Oracle:", e)
        raise
