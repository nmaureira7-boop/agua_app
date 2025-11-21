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

import os
import oracledb

def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),          # ADMIN
        password=os.getenv("DB_PASS"),      # contraseña del usuario
        dsn="g41d7b285d304e7_bluedate_high",  # alias exacto del tnsnames.ora
        config_dir="/opt/render/project/src/agua_app/wallet",   # carpeta con los archivos del wallet
        wallet_location="/opt/render/project/src/agua_app/wallet",
        wallet_password=os.getenv("WALLET_PASS")   # clave del wallet desde variable de entorno
    )
