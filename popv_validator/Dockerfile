# popv_validator/Dockerfile
FROM python:3.9-slim-buster
WORKDIR /app

RUN apt-get update && \
    apt-get install -y iproute2 net-tools batctl python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5003

CMD ["/bin/bash", "-c", " \
    echo 'Configurando interfaz BATMAN (bat0) en PoPV Validator...' && \
    ip link add name bat0 type dummy && \
    ip link set dev bat0 up && \
    batctl if add bat0 && \
    echo 'BATMAN en PoPV Validator configurado. Iniciando servicio...' && \
    sleep 3 && \
    /usr/local/bin/python3 validator.py \
"]
