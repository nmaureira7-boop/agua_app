from dotenv import load_dotenv
import os
import oracledb

# Cargar variables desde el archivo .env (solo en local, Render usa Environment Variables)
load_dotenv()

def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),          # ADMIN
        password=os.getenv("DB_PASS"),      # contraseña del usuario
        dsn="bluedate_tp",                  # alias exacto definido en tnsnames.ora
        config_dir="/opt/render/project/src/wallet",   # 👈 carpeta en la raíz del repo
        wallet_location="/opt/render/project/src/wallet",
        wallet_password=os.getenv("WALLET_PASS")       # clave del wallet desde variable de entorno
    )
