FROM python:3.11-slim

# Dependencias para OpenCV + Tesseract + Redis client
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libaio-dev \
    redis-tools \
    && apt-get clean

# Directorio de trabajo (Render usa esta ruta)
WORKDIR /opt/render/project/src

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto (incluye wallet/, start.sh, etc.)
COPY . .

# Dar permisos de ejecución al script de arranque
RUN chmod +x start.sh

# Exponer puerto de Flask/Gunicorn
EXPOSE 5000

# Usar el script de arranque para levantar Redis + Gunicorn + Celery
CMD ["./start.sh"]
