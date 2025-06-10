# flask/app.py
from flask import Flask, render_template, request, jsonify
import requests
import os
import subprocess
import redis
import json
import time # Para sleep en health checks

app = Flask(__name__)

# URLs de tus servicios (ahora usando las IPs asignadas en docker-compose.yml)
ECDSA_SERVICE_URL = os.getenv("ECDSA_SERVICE_URL")
SZS_STARK_SERVICE_URL = os.getenv("SZS_STARK_SERVICE_URL")
VALIDATOR_SERVICE_URL = os.getenv("VALIDATOR_SERVICE_URL")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

r = None # Inicializar a None

def connect_to_redis():
    global r
    try:
        r_temp = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True, socket_connect_timeout=1)
        r_temp.ping()
        r = r_temp
        print("Flask: Conectado a Redis con éxito.")
        return True
    except redis.exceptions.ConnectionError as e:
        print(f"Flask: Error al conectar a Redis en {REDIS_HOST}:{REDIS_PORT}: {e}")
        r = None
        return False

# Intentar conectar a Redis al inicio
connect_to_redis()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    data = request.json
    transaction_data = data.get('transaction_data')

    if not transaction_data:
        return jsonify({"status": "error", "message": "Transaction data is missing."}), 400

    print(f"Flask: Recibida transacción para procesar: {transaction_data}")

    # 1. Enviar a ECDSA para firmar
    signed_tx = None
    try:
        response = requests.post(f"{ECDSA_SERVICE_URL}/sign", json={'data': transaction_data}, timeout=5)
        response.raise_for_status()
        signed_tx = response.json()
        print(f"Flask: Transacción firmada por ECDSA: {signed_tx}")
    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Error en el servicio ECDSA ({ECDSA_SERVICE_URL}): {e}"}), 500

    # 2. Enviar a SZS-STARK para generar prueba (si aplica)
    stark_proof = None
    try:
        response = requests.post(f"{SZS_STARK_SERVICE_URL}/generate_proof", json={'signed_tx_data': signed_tx['signed_data']}, timeout=5)
        response.raise_for_status()
        stark_proof = response.json()
        print(f"Flask: Prueba STARK generada: {stark_proof}")
    except requests.exceptions.RequestException as e:
        print(f"Flask: Advertencia: Error en el servicio SZS-STARK ({SZS_STARK_SERVICE_URL}): {e}. Continuando sin prueba STARK.")

    # 3. Almacenar en Redis para que el validador la tome
    if not r and not connect_to_redis(): # Reintentar conexión a Redis
        return jsonify({"status": "error", "message": "Redis no está conectado. No se puede almacenar la transacción."}), 500

    try:
        full_transaction = {
            "original_data": transaction_data,
            "signed_data": signed_tx.get('signed_data'),
            "public_key": signed_tx.get('public_key'),
            "stark_proof": stark_proof
        }
        r.lpush('pending_transactions', json.dumps(full_transaction))
        print(f"Flask: Transacción enviada a Redis: {full_transaction}")
        return jsonify({"status": "success", "message": "Transaction sent for validation", "transaction": full_transaction}), 200
    except redis.exceptions.ConnectionError as e:
        print(f"Flask: Error de conexión con Redis al almacenar: {e}")
        r = None # Marcar como desconectado
        return jsonify({"status": "error", "message": f"Error de conexión con Redis: {e}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Error al almacenar en Redis: {e}"}), 500

@app.route('/network_status')
def network_status():
    status_data = {}

    # 1. Obtener la tabla de originators de BATMAN desde este contenedor
    try:
        result = subprocess.run(["batctl", "o", "bat0"], capture_output=True, text=True, check=True)
        status_data["batman_originators_local"] = result.stdout
    except subprocess.CalledLProcessError as e:
        status_data["batman_originators_local_error"] = f"Error ejecutando 'batctl o bat0': {e.stderr}"
    except FileNotFoundError:
        status_data["batman_originators_local_error"] = "batctl no encontrado en el contenedor Flask."
    except Exception as e:
        status_data["batman_originators_local_error"] = f"Error inesperado al obtener originators de BATMAN: {e}"

    # 2. Obtener la tabla de vecinos de BATMAN desde este contenedor
    try:
        result = subprocess.run(["batctl", "n", "bat0"], capture_output=True, text=True, check=True)
        status_data["batman_neighbors_local"] = result.stdout
    except subprocess.CalledProcessError as e:
        status_data["batman_neighbors_local_error"] = f"Error ejecutando 'batctl n bat0': {e.stderr}"
    except Exception as e:
        status_data["batman_neighbors_local_error"] = f"Error inesperado al obtener vecinos de BATMAN: {e}"

    # 3. Comprobar la comunicación con otros servicios (usando sus IPs)
    node_communication = {}
    services = {
        "ECDSA": ECDSA_SERVICE_URL,
        "SZS-STARK": SZS_STARK_SERVICE_URL,
        "Validator": VALIDATOR_SERVICE_URL
    }
    for service_name, url in services.items():
        try:
            response = requests.get(url + "/health", timeout=1)
            if response.status_code == 200 and response.json().get('status') == 'ok':
                node_communication[service_name] = "OK"
            else:
                node_communication[service_name] = f"Error HTTP {response.status_code} o respuesta inválida"
        except requests.exceptions.ConnectionError:
            node_communication[service_name] = "No Conectado"
        except requests.exceptions.Timeout:
            node_communication[service_name] = "Timeout"
        except Exception as e:
            node_communication[service_name] = f"Error: {e}"
    status_data["node_communication_status"] = node_communication

    # 4. Obtener el estado de la cola de transacciones pendientes en Redis
    if not r and not connect_to_redis():
        status_data["redis_pending_transactions_error"] = "Redis no está conectado."
    else:
        try:
            pending_count = r.llen('pending_transactions')
            status_data["redis_pending_transactions"] = pending_count
        except redis.exceptions.ConnectionError:
            status_data["redis_pending_transactions_error"] = "No se pudo conectar a Redis para obtener transacciones pendientes."
            r = None

    # 5. Obtener el estado de la blockchain del Validador PoPV
    try:
        response = requests.get(f"{VALIDATOR_SERVICE_URL}/blockchain_status", timeout=1)
        response.raise_for_status()
        status_data["blockchain_status_from_validator"] = response.json()
    except requests.exceptions.ConnectionError:
        status_data["blockchain_status_from_validator_error"] = "No se pudo conectar al Validador PoPV."
    except requests.exceptions.RequestException as e:
        status_data["blockchain_status_from_validator_error"] = f"Error al obtener estado del validador: {e}"

    return jsonify(status_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
