# conversion_service.py
from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get('EXCHANGERATE_API_KEY', "b24da259d386d7c275ddf332e7ec0638") # Use environment variable first
HISTORY_SERVICE_URL = os.environ.get('HISTORY_SERVICE_URL', 'http://127.0.0.1:5002/api/history') # Fallback for local testing

@app.route('/api/convert', methods=['GET'])
def convert_currency_api():
    from_currency = request.args.get('from_currency')
    to_currency = request.args.get('to_currency')
    amount = request.args.get('amount', type=float)

    # Validation
    if not from_currency or not to_currency or amount is None:
        return jsonify({"error": "Missing parameters: from_currency, to_currency, and amount are required."}), 400

    if not (from_currency.isalpha() and len(from_currency) == 3 and
            to_currency.isalpha() and len(to_currency) == 3):
        return jsonify({"error": "Currency codes must be 3-letter alphabetical (e.g., USD, INR)."}), 400

    # Call external ExchangeRate.host API
    url = "https://api.exchangerate.host/convert"
    params = {
        "from": from_currency.upper(),
        "to": to_currency.upper(),
        "amount": amount,
        "access_key": API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get('success', False):
            error_info = data.get('error', {}).get('info', 'Unknown error from external API.')
            return jsonify({"error": f"External API conversion failed: {error_info}"}), 500

        converted_amount = data.get('result')

        # Prepare history data
        history_data = {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "original_amount": amount,
            "converted_amount": converted_amount
        }

        # Call history service to save the conversion record (fire and forget)
        try:
            # You may want to check response or handle errors here if needed
            requests.post(HISTORY_SERVICE_URL, json=history_data, timeout=2)
        except Exception as e:
            # Log error or ignore to not disrupt conversion service response
            print(f"Warning: Failed to save history record: {e}")

        return jsonify({
            "converted_amount": converted_amount,
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "original_amount": amount
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to connect to external currency API: {e}"}), 500
    except Exception as e:
        return jsonify({"error": f"An internal server error occurred: {e}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
