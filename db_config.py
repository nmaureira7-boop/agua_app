import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_path = "/opt/render/project/src/wallet"

    dsn = """
    (description=
        (retry_count=20)
        (retry_delay=3)
        (address=(protocol=tcps)(port=1522)(host=adb.sa-santiago-1.oraclecloud.com))
        (connect_data=(service_name=g41d7b285d304e7_bluedate_tp.adb.oraclecloud.com))
        (security=(ssl_server_dn_match=yes))
    )
    """

    try:
        return oracledb.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            dsn=dsn,
            config_dir=wallet_path,
            wallet_location=wallet_path,
            wallet_password=os.getenv("WALLET_PASS")
        )
    except Exception as e:
        print("Error al conectar a Oracle:", e)
        raise
