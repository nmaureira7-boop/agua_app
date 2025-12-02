FROM python:3.11-slim

# Dependencias necesarias (OracleDB + utilidades básicas)
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    libaio-dev \
    && apt-get clean

# Directorio de trabajo
WORKDIR /opt/render/project/src

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar TODO el proyecto
COPY . .

# Dar permisos de ejecución al script de arranque
RUN chmod +x start.sh

# Exponer puerto de Flask/Gunicorn
EXPOSE 5000

# Usar el script de arranque (solo Gunicorn ahora)
CMD ["./start.sh"]
