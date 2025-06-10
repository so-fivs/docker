# szsstark/szsstark_service.py
from flask import Flask, request, jsonify
import hashlib

app = Flask(__name__)

@app.route('/generate_proof', methods=['POST'])
def generate_proof():
    signed_tx_data = request.json.get('signed_tx_data')
    if not signed_tx_data:
        return jsonify({"error": "No signed transaction data provided"}), 400

    print(f"SZS-STARK Service: Recibida petición para generar prueba para: '{signed_tx_data}'")
    # SIMULACIÓN REAL de una prueba STARK
    proof_hash = hashlib.sha256(signed_tx_data.encode('utf-8') + b"stark_salt").hexdigest()
    stark_proof = {
        "proof_id": "STARK-PROOF-" + proof_hash[:8],
        "message": f"Simulated STARK proof for data: {signed_tx_data}",
        "valid": True # Siempre válida en esta simulación
    }
    print(f"SZS-STARK Service: Prueba generada: {stark_proof}")
    return jsonify(stark_proof)

@app.route('/verify_proof', methods=['POST'])
def verify_proof():
    proof_data = request.json.get('proof_data')
    original_data = request.json.get('original_data')

    if not proof_data or not original_data:
        return jsonify({"error": "Missing proof_data or original_data"}), 400

    print(f"SZS-STARK Service: Recibida petición para verificar prueba: {proof_data}")
    # SIMULACIÓN REAL de la verificación de una prueba STARK
    # En una implementación real, esto sería un cálculo criptográfico complejo.
    is_valid = (proof_data.get('valid') == True) # Asumimos la validez de la simulación
    print(f"SZS-STARK Service: Prueba verificada con resultado: {is_valid}")
    return jsonify({"is_valid": is_valid})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "SZS-STARK"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
