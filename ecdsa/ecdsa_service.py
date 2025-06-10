# ecdsa/ecdsa_service.py
from flask import Flask, request, jsonify
from ecdsa import SigningKey, SECP256k1, VerifyingKey
import hashlib

app = Flask(__name__)

# Generar una clave de firma para este nodo (para la simulación)
sk = SigningKey.generate(curve=SECP256k1)
vk = sk.get_verifying_key()
print(f"ECDSA Service: Public Key for this node: {vk.to_string().hex()}")

@app.route('/sign', methods=['POST'])
def sign_data():
    data = request.json.get('data')
    if not data:
        return jsonify({"error": "No data provided"}), 400

    print(f"ECDSA Service: Recibida petición para firmar: '{data}'")
    data_hash = hashlib.sha256(data.encode('utf-8')).digest()
    signature = sk.sign(data_hash)

    return jsonify({
        "original_data": data,
        "signed_data": signature.hex(),
        "public_key": vk.to_string().hex()
    })

@app.route('/verify', methods=['POST'])
def verify_data():
    signed_data_hex = request.json.get('signed_data')
    original_data = request.json.get('original_data')
    public_key_hex = request.json.get('public_key')

    if not all([signed_data_hex, original_data, public_key_hex]):
        return jsonify({"error": "Missing data"}), 400

    try:
        signature = bytes.fromhex(signed_data_hex)
        public_key = VerifyingKey.from_string(bytes.fromhex(public_key_hex), curve=SECP256k1)
        original_data_hash = hashlib.sha256(original_data.encode('utf-8')).digest()

        is_valid = public_key.verify(signature, original_data_hash)
        print(f"ECDSA Service: Verificación de firma para '{original_data}' con resultado: {is_valid}")
        return jsonify({"is_valid": is_valid})
    except Exception as e:
        print(f"ECDSA Service: Error en verificación de firma: {e}")
        return jsonify({"error": f"Verification failed: {e}"}), 400

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "service": "ECDSA"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
