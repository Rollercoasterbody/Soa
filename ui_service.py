from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# URL for the ConversionService API
CONVERSION_SERVICE_URL = os.environ.get("CONVERSION_URL", "https://conversion-service-placeholder.onrender.com/api/convert")
# URL for the HistoryService API
HISTORY_SERVICE_URL = os.environ.get("HISTORY_URL", "https://history-service-placeholder.onrender.com/api/save")

# HTML template (main form)
FORM_HTML = """
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Distributed Currency Converter</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f7f6;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            color: #333;
        }
        .container {
            background-color: #ffffff;
            padding: 30px 40px;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 450px;
            text-align: center;
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 25px;
            font-size: 2em;
        }
        form {
            text-align: left;
        }
        .form-group {
            margin-bottom: 18px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #555;
            font-size: 0.95em;
        }
        input[type="number"],
        input[type="text"] {
            width: calc(100% - 20px);
            padding: 12px 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 1em;
            box-sizing: border-box;
        }
        input[type="submit"] {
            background-color: #28a745;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1.1em;
            font-weight: bold;
            margin-top: 20px;
            transition: background-color 0.3s ease;
            width: 100%;
        }
        input[type="submit"]:hover {
            background-color: #218838;
        }
        .result-box {
            background-color: #e9f7ef;
            border: 1px solid #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-top: 25px;
            font-size: 1.1em;
            font-weight: bold;
            text-align: center;
        }
        .error-message {
            color: #dc3545;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 8px;
            margin-top: 25px;
            font-size: 1em;
            text-align: center;
        }
        p {
            margin: 5px 0;
        }
        .history-button { /* New CSS for the history button */
            display: inline-block;
            background-color: #007bff; /* A nice blue */
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            text-decoration: none; /* Remove underline from link */
            transition: background-color 0.3s ease;
        }
        .history-button:hover { /* Hover effect for the history button */
            background-color: #0056b3; /* Darker blue on hover */
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Distributed Currency Converter</h1>
        <form action="/convert" method="get">
            <div class="form-group">
                <label for="amount">Amount:</label>
                <input type="number" step="any" id="amount" name="amount" required placeholder="e.g., 100" value="{{ amount if amount is not none else '' }}">
            </div>
            <div class="form-group">
                <label for="from">From Currency (e.g., USD):</label>
                <input type="text" id="from" name="from" required placeholder="e.g., USD" maxlength="3" pattern="[A-Za-z]{3}" title="Please enter a 3-letter currency code (e.g., USD)" value="{{ from_currency if from_currency is not none else '' }}">
            </div>
            <div class="form-group">
                <label for="to">To Currency (e.g., INR):</label>
                <input type="text" id="to" name="to" required placeholder="e.g., INR" maxlength="3" pattern="[A-Za-z]{3}" title="Please enter a 3-letter currency code (e.g., INR)" value="{{ to_currency if to_currency is not none else '' }}">
            </div>
            <input type="submit" value="Convert">

            <div style="margin-top: 20px;">
                <a href="/history" class="history-button">View Conversion History</a>
            </div>
            </form>

        {% if result %}
            <div class="result-box">
                <p>{{ original_amount }} {{ from_currency }} = {{ result }} {{ to_currency }}</p>
            </div>
        {% elif error %}
            <div class="error-message">
                <p>Error: {{ error }}</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(FORM_HTML, amount=None, from_currency=None, to_currency=None)

@app.route('/convert', methods=['GET'])
def convert_currency():
    from_currency = request.args.get('from')
    to_currency = request.args.get('to')
    amount = request.args.get('amount', type=float)

    # Basic client-side input validation
    if not from_currency or not to_currency or amount is None:
        error_msg = "Please provide all required fields: Amount, From Currency, and To Currency."
        return render_template_string(FORM_HTML, error=error_msg, amount=amount, from_currency=from_currency, to_currency=to_currency)

    if not (from_currency.isalpha() and len(from_currency) == 3 and
            to_currency.isalpha() and len(to_currency) == 3):
        error_msg = "Currency codes must be 3-letter alphabetical (e.g., USD, INR)."
        return render_template_string(FORM_HTML, error=error_msg, amount=amount, from_currency=from_currency, to_currency=to_currency)

    # Make an internal API call to the ConversionService
    try:
        params = {
            "from_currency": from_currency.upper(),
            "to_currency": to_currency.upper(),
            "amount": amount
        }
        conversion_response = requests.get(CONVERSION_SERVICE_URL, params=params)
        conversion_response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        data = conversion_response.json()

        if "error" in data:
            error_msg = data["error"]
            return render_template_string(FORM_HTML, error=error_msg,
                                          amount=amount, from_currency=from_currency, to_currency=to_currency)
        else:
            converted_amount = data.get('converted_amount')
            original_amount = data.get('original_amount') # Get original amount from conversion service response
            return render_template_string(FORM_HTML,
                                          result=round(converted_amount, 2),
                                          original_amount=original_amount,
                                          amount=amount, # Keep this for re-populating form
                                          from_currency=data.get('from_currency'),
                                          to_currency=data.get('to_currency'))

    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to the currency conversion service. Please ensure it is running."
        return render_template_string(FORM_HTML, error=error_msg, amount=amount, from_currency=from_currency, to_currency=to_currency)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Conversion service returned an error: {e}"
        # Try to parse JSON error if available
        try:
            error_data = conversion_response.json()
            error_msg = error_data.get('error', error_msg)
        except ValueError: # JSONDecodeError
            pass
        return render_template_string(FORM_HTML, error=error_msg, amount=amount, from_currency=from_currency, to_currency=to_currency)
    except Exception as e:
        error_msg = f"An unexpected error occurred: {e}"
        return render_template_string(FORM_HTML, error=error_msg, amount=amount, from_currency=from_currency, to_currency=to_currency)

# NEW: Route to display conversion history
@app.route('/history', methods=['GET'])
def view_history():
    try:
        # Call the history service to get all records
        history_response = requests.get(HISTORY_SERVICE_URL)
        history_response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        history_data = history_response.json()

        # Build HTML to display the history
        history_html = """
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Conversion History</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f7f6;
                    margin: 0;
                    display: flex;
                    flex-direction: column; /* Changed to column */
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    color: #333;
                }
                .container {
                    background-color: #ffffff;
                    padding: 30px 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
                    width: 100%;
                    max-width: 600px; /* Increased max-width */
                    text-align: center;
                    margin-bottom: 20px; /* Add some space below */
                }
                h1 {
                    color: #2c3e50;
                    margin-bottom: 25px;
                    font-size: 2em;
                }
                .history-list {
                    list-style: none;
                    padding: 0;
                }
                .history-item {
                    background-color: #e9f7ef;
                    border: 1px solid #d4edda;
                    color: #155724;
                    padding: 10px 15px;
                    margin-bottom: 10px;
                    border-radius: 5px;
                    text-align: left;
                    font-size: 1.0em;
                }
                .back-button {
                    display: inline-block;
                    background-color: #6c757d; /* Grey */
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 1em;
                    text-decoration: none;
                    transition: background-color 0.3s ease;
                }
                .back-button:hover {
                    background-color: #5a6268;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Conversion History</h1>
                {% if history_data %}
                    <ul class="history-list">
                    {% for item in history_data %}
                        <li class="history-item">
                            {{ item.original_amount }} {{ item.from_currency }} = {{ item.converted_amount | round(2) }} {{ item.to_currency }}
                        </li>
                    {% endfor %}
                    </ul>
                {% else %}
                    <p>No conversion history found.</p>
                {% endif %}
                <a href="/" class="back-button">Back to Converter</a>
            </div>
        </body>
        </html>
        """
        return render_template_string(history_html, history_data=history_data)

    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to the history service. Please ensure it is running."
        return render_template_string(FORM_HTML, error=error_msg) # Render main form with error
    except requests.exceptions.HTTPError as e:
        error_msg = f"History service returned an error: {e}"
        try:
            error_data = history_response.json()
            error_msg = error_data.get('error', error_msg)
        except Exception:
            pass
        return render_template_string(FORM_HTML, error=error_msg) # Render main form with error
    except Exception as e:
        error_msg = f"An unexpected error occurred while fetching history: {e}"
        return render_template_string(FORM_HTML, error=error_msg) # Render main form with error


if __name__ == '__main__':
    # Use a different port for the UI service
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)