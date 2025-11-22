FROM python:3.11-slim

# Dependencias para Oracle
RUN apt-get update && apt-get install -y wget unzip libaio1 tesseract-ocr libtesseract-dev && \
    apt-get clean

# Descargar e instalar Oracle Instant Client (Basic Lite)
RUN wget https://download.oracle.com/otn_software/linux/instantclient/213000/instantclient-basiclite-linux.x64-21.3.0.0.0.zip -O instantclient.zip && \
    unzip instantclient.zip -d /opt/oracle && \
    rm instantclient.zip && \
    echo /opt/oracle/instantclient_21_3 > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proyecto
COPY . .

# Copiar wallet a la ruta donde Oracle lo exige
RUN mkdir -p /opt/render/project/src/wallet
RUN cp -r wallet/* /opt/render/project/src/wallet/
RUN chmod -R 755 /opt/render/project/src/wallet

EXPOSE 5000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
