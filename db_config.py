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

import oracledb
import os

import os
import oracledb

def get_connection():
    return oracledb.connect(
        user=os.getenv("DB_USER"),          # ADMIN
        password=os.getenv("DB_PASS"),      # tu contraseña
        dsn="g41d7b285d304e7_bluedate_high.adb.oraclecloud.com",  # servicio del wallet
        config_dir="/opt/render/project/src/wallet",   # carpeta con los archivos del wallet
        wallet_location="/opt/render/project/src/wallet",
        wallet_password="WALLET_PASS"           # el que definiste al descargar el wallet
    )
