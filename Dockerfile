FROM python:3.11-slim

# Dependencias para OpenCV + Tesseract
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    tesseract-ocr \
    libtesseract-dev \
    libgl1 \
    libglib2.0-0 \
    libaio-dev \
    && apt-get clean

# Render coloca tu proyecto en /opt/render/project/src
# Usamos la misma ruta para evitar problemas con wallet
WORKDIR /opt/render/project/src

# Copiar requirements
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto (incluye wallet/)
COPY . .

# Exponer puerto
EXPOSE 5000

# Iniciar servidor
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
