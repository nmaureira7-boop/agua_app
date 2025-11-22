FROM python:3.13-slim

# =========================
# 1. Instalar librerías del sistema
# =========================
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    libaio1 \
    unzip \
    && apt-get clean

WORKDIR /app

# =========================
# 2. Copiar requirements e instalar
# =========================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# =========================
# 3. Copiar aplicación completa
# =========================
COPY . .

# =========================
# 4. Copiar Wallet (IMPORTANTE)
# =========================
# Render construye el contenedor en /app
# Por eso el wallet debe quedar en /app/wallet
COPY wallet /app/wallet

# =========================
# 5. Variables de entorno Oracle
# =========================
ENV TNS_ADMIN=/app/wallet

# =========================
# 6. Puerto de Flask
# =========================
EXPOSE 5000

# =========================
# 7. Comando de inicio
# =========================
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
