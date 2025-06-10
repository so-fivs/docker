# flask/app.py
from flask import Flask, render_template, request, jsonify
import os
import requests # Necesitarás esta librería para hacer llamadas HTTP a otros servicios
import json # Para parsear el JSON de la transacción si es necesario
import redis # Para interactuar con Redis
# import subprocess # Ya no necesitamos esta librería si no ejecutamos comandos externos como batctl

app = Flask(__name__)

# Configuración de los servicios (debe coincidir con tus variables de entorno en docker-compose.yml)
ECDSA_SERVICE_URL = os.getenv('ECDSA_SERVICE_URL', 'http://ecdsa:5001')
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
SZS_STARK_SERVICE_URL = os.getenv('SZS_STARK_SERVICE_URL', 'http://szsstark:5002')
VALIDATOR_SERVICE_URL = os.getenv('VALIDATOR_SERVICE_URL', 'http://popv_validator:5003')

# Configuración del logging para Flask (útil para ver los mensajes de print)
import logging
logging.basicConfig(level=logging.INFO) # Puedes cambiar a logging.DEBUG para más detalles
app.logger.setLevel(logging.INFO)

# Conexión a Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    app.logger.info("Flask: Conectado a Redis con éxito.")
except Exception as e:
    app.logger.error(f"Flask: Error al conectar a Redis: {e}")
    r = None # Asegúrate de manejar el caso donde Redis no está disponible

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_transaction', methods=['POST'])
def send_transaction():
    try:
        data = request.get_json() # Obtiene los datos JSON enviados desde el JavaScript
        transaction_data = data.get('transaction_data')

        if not transaction_data:
            return jsonify({"error": "Transaction data is missing"}), 400

        # Aquí iría la lógica para procesar la transacción:
        # 1. Parsing de la transacción (ej. sender, recipient, amount)
        try:
            # Asume que transaction_data es un string como "sender:Alice,receiver:Bob,amount:10"
            # o podrías enviarlo directamente como JSON desde el frontend para simplificar
            parts = [p.strip().split(':') for p in transaction_data.split(',')]
            transaction_dict = {k.strip(): v.strip() for k, v in parts if len(p) == 2}
            sender = transaction_dict.get('sender')
            recipient = transaction_dict.get('recipient')
            amount = transaction_dict.get('amount')
            # Convierte amount a float o int
            try:
                amount = float(amount)
            except ValueError:
                return jsonify({"error": "Invalid amount format"}), 400

            # Validar que los campos esenciales estén presentes
            if not all([sender, recipient, amount is not None]):
                return jsonify({"error": "Missing transaction fields (sender, recipient, amount)"}), 400

            # 2. Llamar al servicio ECDSA para firmar
            ecdsa_response = requests.post(f"{ECDSA_SERVICE_URL}/sign", json={"transaction": transaction_dict})
            ecdsa_response.raise_for_status() # Lanza un error para códigos de estado HTTP 4xx/5xx
            signed_transaction = ecdsa_response.json()
            app.logger.info(f"Signed transaction from ECDSA: {signed_transaction}")


            # 3. Llamar al servicio SZS-STARK para generar la prueba (ejemplo)
            stark_response = requests.post(f"{SZS_STARK_SERVICE_URL}/generate_proof", json={"data": signed_transaction})
            stark_response.raise_for_status()
            stark_proof = stark_response.json()
            app.logger.info(f"STARK proof generated: {stark_proof}")

            # Combina la transacción con la prueba y la firma
            final_transaction = {
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "signature": signed_transaction.get("signature"),
                "public_key": signed_transaction.get("public_key"),
                "stark_proof": stark_proof.get("proof")
            }

            # 4. Almacenar la transacción final en Redis como pendiente
            if r:
                r.lpush('pending_transactions', json.dumps(final_transaction))
                app.logger.info(f"Transaction added to Redis pending queue: {final_transaction}")
            else:
                app.logger.error("Redis connection not available.")
                return jsonify({"error": "Redis not connected"}), 500

            # 5. Notificar al validador (opcional, el validador podría estar polling Redis)
            # Si el validador necesita ser notificado, harías otra request POST aquí.
            # requests.post(f"{VALIDATOR_SERVICE_URL}/new_pending_tx")

            return jsonify({"status": "Transaction received and processed", "transaction": final_transaction}), 200

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format in transaction data"}), 400
        except requests.exceptions.RequestException as req_err:
            app.logger.error(f"Error communicating with external service: {req_err}")
            return jsonify({"error": f"Failed to communicate with external service: {req_err}"}), 500
        except Exception as e:
            app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return jsonify({"error": f"An unexpected server error occurred: {e}"}), 500

    except Exception as e:
        app.logger.error(f"Error processing transaction POST request: {e}", exc_info=True)
        return jsonify({"error": f"Invalid request or server error: {e}"}), 400

# Añade la ruta para obtener el estado de la red (si no la tienes ya)
@app.route('/network_status')
def get_network_status():
    status = {}

    # Aquí hemos comentado/eliminado las llamadas a batctl porque el contenedor Docker
    # no tiene acceso directo a las interfaces de red del host (VM).
    # La información de BATMAN-adv debe ser obtenida directamente desde la VM de Ubuntu.
    status['batman_status'] = "BATMAN-adv runs on the host VM, not directly in this container."
    status['batman_originators_local'] = "N/A (check VM host with 'sudo batctl o')"
    status['batman_neighbors_local'] = "N/A (check VM host with 'sudo batctl n')"


    # Estado de comunicación entre nodos Docker (esto SÍ debería funcionar)
    node_comm_status = {}
    try:
        response = requests.get(f"{ECDSA_SERVICE_URL}/status", timeout=2)
        node_comm_status['ecdsa'] = "OK" if response.status_code == 200 else f"Error: {response.status_code}"
    except requests.exceptions.RequestException:
        node_comm_status['ecdsa'] = "Unreachable"

    try:
        response = requests.get(f"{SZS_STARK_SERVICE_URL}/status", timeout=2)
        node_comm_status['szsstark'] = "OK" if response.status_code == 200 else f"Error: {response.status_code}"
    except requests.exceptions.RequestException:
        node_comm_status['szsstark'] = "Unreachable"

    try:
        response = requests.get(f"{VALIDATOR_SERVICE_URL}/status", timeout=2)
        node_comm_status['popv_validator'] = "OK" if response.status_code == 200 else f"Error: {response.status_code}"
    except requests.exceptions.RequestException:
        node_comm_status['popv_validator'] = "Unreachable"

    status['node_communication_status'] = node_comm_status

    # Redis Pending Transactions (esto SÍ debería funcionar)
    if r:
        try:
            pending_tx_count = r.llen('pending_transactions')
            status['redis_pending_transactions'] = pending_tx_count
        except Exception as e:
            status['redis_pending_transactions_error'] = f"Error fetching pending transactions from Redis: {e}"
    else:
        status['redis_pending_transactions_error'] = "Redis connection not available"

    # Blockchain Status from Validator (esto SÍ debería funcionar)
    try:
        validator_response = requests.get(f"{VALIDATOR_SERVICE_URL}/blockchain", timeout=5)
        validator_response.raise_for_status()
        status['blockchain_status_from_validator'] = validator_response.json()
    except requests.exceptions.RequestException as e:
        status['blockchain_status_from_validator_error'] = f"Error fetching blockchain status from Validator: {e}"

    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
