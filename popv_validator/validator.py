# popv_validator/validator.py
import time
import json
import redis
import requests
import hashlib
import os
from threading import Thread, Event
from flask import Flask, jsonify

app_flask = Flask(__name__)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
ECDSA_SERVICE_URL = os.getenv("ECDSA_SERVICE_URL")
SZS_STARK_SERVICE_URL = os.getenv("SZS_STARK_SERVICE_URL")

blockchain = []
r = None

def connect_to_redis():
    global r
    try:
        r_temp = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True, socket_connect_timeout=1)
        r_temp.ping()
        r = r_temp
        print("Validator: Conectado a Redis con éxito.")
        return True
    except redis.exceptions.ConnectionError as e:
        print(f"Validator: Error al conectar a Redis en {REDIS_HOST}:{REDIS_PORT}: {e}")
        r = None
        return False

connect_to_redis() # Intentar conectar al inicio

stop_event = Event()

def validate_and_process_transactions():
    global blockchain
    print("Validator: Iniciando procesador de transacciones...")
    while not stop_event.is_set():
        if not r and not connect_to_redis(): # Reintentar conexión a Redis
            time.sleep(1)
            continue

        try:
            item = r.blpop('pending_transactions', timeout=5)
            if item:
                queue_name, transaction_json = item
                transaction = json.loads(transaction_json)
                print(f"\nValidator: Recibida transacción de Redis: {transaction.get('original_data', 'N/A')}")

                is_valid = True # Asume válido hasta que se demuestre lo contrario

                # 1. Verificar firma ECDSA
                if transaction.get('signed_data') and transaction.get('original_data') and transaction.get('public_key'):
                    try:
                        verify_response = requests.post(
                            f"{ECDSA_SERVICE_URL}/verify",
                            json={
                                'signed_data': transaction['signed_data'],
                                'original_data': transaction['original_data'],
                                'public_key': transaction['public_key']
                            },
                            timeout=2
                        )
                        verify_response.raise_for_status()
                        ecdsa_valid = verify_response.json().get('is_valid')
                        if not ecdsa_valid:
                            is_valid = False
                            print("Validator: Firma ECDSA inválida.")
                    except requests.exceptions.RequestException as e:
                        print(f"Validator: Error al verificar firma ECDSA ({ECDSA_SERVICE_URL}): {e}")
                        is_valid = False
                else:
                    print("Validator: Datos de firma incompletos o ausentes, asumiendo inválida.")
                    is_valid = False

                # 2. Verificar prueba STARK (si existe)
                if transaction.get('stark_proof'):
                    try:
                        verify_stark_response = requests.post(
                            f"{SZS_STARK_SERVICE_URL}/verify_proof",
                            json={
                                'proof_data': transaction['stark_proof'],
                                'original_data': transaction['original_data']
                            },
                            timeout=2
                        )
                        verify_stark_response.raise_for_status()
                        stark_valid = verify_stark_response.json().get('is_valid')
                        if not stark_valid:
                            is_valid = False
                            print("Validator: Prueba STARK inválida.")
                    except requests.exceptions.RequestException as e:
                        print(f"Validator: Error al verificar prueba STARK ({SZS_STARK_SERVICE_URL}): {e}")
                        is_valid = False
                else:
                    print("Validator: No hay prueba STARK para verificar.")

                # 3. Aplicar lógica de consenso PoPV (EJEMPLO SIMPLE: solo acepta números pares)
                # Aquí es donde implementarías tu lógica específica de PoPV
                print(f"Validator: Aplicando lógica PoPV para '{transaction.get('original_data')}'...")
                if transaction.get('original_data') and isinstance(transaction['original_data'], str) and transaction['original_data'].isdigit():
                    if int(transaction['original_data']) % 2 != 0:
                        is_valid = False
                        print(f"Validator: PoPV falló: la transacción contiene un número impar ({transaction['original_data']}).")
                    else:
                        print(f"Validator: PoPV OK: la transacción contiene un número par ({transaction['original_data']}).")
                else:
                    print("Validator: PoPV OK: la transacción no es numérica o no requiere esta validación.")


                # --- Proceso de Bloqueo ---
                if is_valid:
                    block_data = {
                        "timestamp": time.time(),
                        "transactions": [transaction], # Un bloque simple con 1 trans
                        "previous_hash": blockchain[-1]['hash'] if blockchain else "0",
                        "validator_id": "PoPV-Validator-001",
                        "block_number": len(blockchain) + 1
                    }
                    block_hash = hashlib.sha256(json.dumps(block_data, sort_keys=True).encode('utf-8')).hexdigest()
                    block_data['hash'] = block_hash
                    blockchain.append(block_data)
                    print(f"Validator: Transacción validada y añadida al bloque #{block_data['block_number']}: {block_hash}")
                    if r:
                        r.publish('new_block_channel', json.dumps(block_data)) # Opcional: notificar otros servicios
                else:
                    print(f"Validator: Transacción inválida, descartada: {transaction.get('original_data', 'N/A')}")
        except redis.exceptions.ConnectionError:
            print("Validator: Error de conexión con Redis. Reintentando en 1 segundo...")
            r = None # Marcar como desconectado
            time.sleep(1)
        except json.JSONDecodeError as e:
            print(f"Validator: Error al decodificar JSON de Redis: {e}. Descartando mensaje.")
        except Exception as e:
            print(f"Validator: Error inesperado en el procesador de transacciones: {e}")

        time.sleep(0.5)

@app_flask.route('/blockchain_status', methods=['GET'])
def blockchain_status():
    return jsonify({
        "status": "ok",
        "chain_length": len(blockchain),
        "last_block": blockchain[-1] if blockchain else "No blocks yet",
        # "all_blocks": blockchain # Descomenta para ver todos los bloques, puede ser largo
    }), 200

@app_flask.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "PoPV Validator"}), 200

def run_flask_api():
    app_flask.run(host='0.0.0.0', port=5003, debug=False, use_reloader=False)

if __name__ == '__main__':
    processor_thread = Thread(target=validate_and_process_transactions)
    processor_thread.daemon = True
    processor_thread.start()

    run_flask_api()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Validator: Shutting down...")
        stop_event.set()
        processor_thread.join(timeout=5)
        print("Validator: Shutdown complete.")
