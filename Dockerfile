FROM python:3.11-slim

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    libaio1 \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean

# Crear carpeta destino del wallet (Render usa /opt/render/project/src)
RUN mkdir -p /opt/render/project/src/wallet

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proyecto
COPY . .

# Copiar wallet a la ruta esperada
COPY wallet /opt/render/project/src/wallet

# Otorgar permisos
RUN chmod -R 755 /opt/render/project/src/wallet

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]

