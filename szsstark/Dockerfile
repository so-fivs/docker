# szsstark/Dockerfile
FROM python:3.9-slim-buster
WORKDIR /app

RUN apt-get update && \
    apt-get install -y iproute2 net-tools batctl python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5002

# ... (otras instrucciones del Dockerfile)

# CMD para configurar BATMAN y luego iniciar la aplicación SZS-STARK
CMD ["/bin/bash", "-c", " \
    echo 'Iniciando servicio SZS-STARK...' && \
    /usr/local/bin/python3 szstark_service.py \
"]
