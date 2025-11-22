FROM python:3.11-slim

# Evitar preguntas del sistema operativo
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias mínimas necesarias
RUN apt-get update && apt-get install -y \
    libaio1 \
    tesseract-ocr \
    libtesseract-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear la carpeta del wallet en la ruta que Render usa
RUN mkdir -p /opt/render/project/src/wallet

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar la app completa
COPY . .

# Copiar el wallet a la ruta exacta donde Oracle lo busca
COPY wallet /opt/render/project/src/wallet

# Dar permisos
RUN chmod -R 755 /opt/render/project/src/wallet

# Exponer puerto
EXPOSE 5000

# Ejecutar gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
