from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# In-memory store for demonstration (use a database for production)
conversion_history = []

@app.route('/api/history', methods=['POST'])
def add_history():
    data = request.get_json()
    required_fields = ['from_currency', 'to_currency', 'original_amount', 'converted_amount']

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required conversion fields"}), 400

    conversion_history.append(data)
    return jsonify({"message": "Conversion saved"}), 201

@app.route('/api/history', methods=['GET'])
def get_history():
    return jsonify(conversion_history), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)