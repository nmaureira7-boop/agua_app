import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

# Importante: activar modo THIN
oracledb.init_oracle_client = lambda *args, **kwargs: None

def get_connection():
    wallet_path = "/opt/render/project/src/wallet"
    
    try:
        return oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            dsn=os.getenv("DB_TNS_NAME"),
            config_dir=wallet_path,
            wallet_location=wallet_path,
            wallet_password=os.getenv("WALLET_PASS")
        )
    except Exception as e:
        print("Error al conectar a Oracle:", e)
        raise
