from flask import Flask, request, jsonify
import os
import time
import hmac
import hashlib
import requests
from dotenv import load_dotenv

# .env-Datei laden (optional, aber empfohlen bei Render)
load_dotenv()

# API-Schlüssel aus Umgebungsvariablen lesen
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")

app = Flask(__name__)

# Funktion zum Senden einer Binance-Futures-Order (MARKET-Order)
def send_binance_order(symbol, side, quantity):
    url = "https://fapi.binance.com/fapi/v1/order"
    timestamp = int(time.time() * 1000)
    params = f"symbol={symbol}&side={side}&type=MARKET&quantity={quantity}&timestamp={timestamp}"
    signature = hmac.new(API_SECRET.encode(), params.encode(), hashlib.sha256).hexdigest()
    params += f"&signature={signature}"

    headers = {
        "X-MBX-APIKEY": API_KEY
    }

    response = requests.post(url, headers=headers, params=params)
    return response.json()

# Webhook-Endpunkt
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook empfangen:", data)

    # Beispielhafte Datenstruktur prüfen
    symbol = data.get('symbol')
    side = data.get('side')
    quantity = data.get('quantity')

    if not all([symbol, side, quantity]):
        return jsonify({'status': 'error', 'message': 'Fehlende Parameter'}), 400

    result = send_binance_order(symbol, side.upper(), quantity)
    return jsonify({'status': 'order gesendet', 'binance_response': result}), 200

# Lokales Testen
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)

