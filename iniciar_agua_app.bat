@echo off
cd /d "%~dp0"
if not exist venv\Scripts\activate.bat (
  echo Entorno virtual no encontrado. Creando uno nuevo...
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install --quiet Flask oracledb pandas xlsxwriter
python app.py
pause