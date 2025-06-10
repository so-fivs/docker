# ecdsa/Dockerfile

FROM python:3.9-slim-buster
WORKDIR /app

# Instalar BATMAN advanced y herramientas de red necesarias
RUN apt-get update && \
    apt-get install -y iproute2 net-tools batctl python3-pip && \
    rm -rf /var/lib/apt/lists/*

# NO CARGAR EL MÓDULO batman_adv AQUÍ. Se carga en el host.
# (Bien, ya quitaste esta línea de tu ejemplo)

# Copiar el archivo de requisitos e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto que usa esta aplicación ECDSA (EXPOSE 5001 está bien)
EXPOSE 5001

# CMD para configurar BATMAN y luego iniciar la aplicación ECDSA
CMD ["/bin/bash", "-c", " \
    echo 'Configurando interfaz BATMAN (bat0) en ECDSA...' && \
    ip link add name bat0 type dummy && \
    ip link set dev bat0 up && \
    batctl if add bat0 && \
    echo 'BATMAN en ECDSA configurado. Iniciando aplicación...' && \
    sleep 3 && \
    /usr/local/bin/python3 app.py \
"]
