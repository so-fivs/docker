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

# ... (otras instrucciones del Dockerfile)

# CMD para configurar BATMAN y luego iniciar el servicio PoPV Validator

CMD ["/bin/bash", "-c", " \
    echo 'Iniciando servicio PoPV Validator...' && \
    /usr/local/bin/python3 validator.py \
"]
