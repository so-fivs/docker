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
# Dentro de flask/Dockerfile, después de COPY . .
COPY . .
# Dentro de flask/Dockerfile, después de COPY . .
RUN apt-get update && apt-get install -y iproute2 batctl && rm -rf /var/lib/apt/lists/*
EXPOSE 5000


# CMD para configurar BATMAN y luego iniciar la aplicación
# ... (otras instrucciones del Dockerfile)

# CMD para configurar BATMAN y luego iniciar la aplicación Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
