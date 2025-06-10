# flask/Dockerfile

FROM python:3.9-slim-buster
WORKDIR /app

# Instalar BATMAN advanced y herramientas de red necesarias
RUN apt-get update && \
    apt-get install -y iproute2 net-tools batctl python3-pip && \
    rm -rf /var/lib/apt/lists/*

# NO CARGAR EL MÓDULO batman_adv AQUÍ. Se carga en el host.
# (Bien que lo hayas quitado)

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000

# CMD para configurar BATMAN y luego iniciar la aplicación
CMD ["/bin/bash", "-c", " \
    echo 'Configurando interfaz BATMAN (bat0) en Flask...' && \
    ip link add name bat0 type dummy && \
    ip link set dev bat0 up && \
    batctl if add bat0 && \
    echo 'BATMAN en Flask configurado. Iniciando aplicación...' && \
    sleep 3 && \
    /usr/local/bin/gunicorn --bind 0.0.0.0:5000 app:app \
"]
