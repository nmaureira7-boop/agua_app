import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_path = "/opt/render/project/src/wallet"

    try:
        oracledb.init_oracle_client(
            lib_dir="/opt/oracle/instantclient_21_3",
            config_dir=wallet_path
        )

        return oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            dsn=os.getenv("DB_TNS_NAME"),  # por ej: "db202501_high"
            wallet_location=wallet_path,
            wallet_password=os.getenv("WALLET_PASS")
        )

    except Exception as e:
        print("Error al conectar a Oracle Autonomous:", e)
        raise
