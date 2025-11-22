FROM python:3.11-slim

# Dependencias del sistema (Oracle + OpenCV)
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio-dev \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean

WORKDIR /app

# Copiar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Exponer puerto
EXPOSE 5000

# Comando de inicio
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
