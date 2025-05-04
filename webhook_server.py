from flask import Flask, request, jsonify
import requests
import time
import hmac
import hashlib
import urllib.parse
import traceback

app = Flask(__name__)

API_KEY = 'DEIN_API_KEY'
API_SECRET = 'DEIN_API_SECRET'

# Aktuellen Preis vom Symbol holen
def get_price(symbol):
    url = f"https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}"
    try:
        response = requests.get(url)
        data = response.json()
        return float(data['price'])
    except Exception as e:
        print("Fehler beim Abrufen des Preises:", e)
        return None

# Berechne kaufbare Menge basierend auf USD-Volumen
def calculate_quantity(volume_usd, symbol):
    price = get_price(symbol)
    if price:
        quantity = volume_usd / price
        return round(quantity, 6)
    return None

# Hole die maximale Preispräzision (Dezimalstellen)
def get_symbol_precision(symbol):
    url = f"https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        response = requests.get(url)
        data = response.json()
        for s in data['symbols']:
            if s['symbol'] == symbol:
                for f in s['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        step_size = float(f['tickSize'])
                        return abs(round(float(f"{step_size:.20f}".rstrip('0')), 8))
        return 2  # Standard
    except Exception as e:
        print("Fehler bei get_symbol_precision:", e)
        return 2

# Leverage setzen
def set_leverage(symbol, leverage):
    url = "https://fapi.binance.com/fapi/v1/leverage"
    params = {
        'symbol': symbol,
        'leverage': leverage,
        'timestamp': int(time.time() * 1000)
    }
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = {
        'X-MBX-APIKEY': API_KEY
    }
    response = requests.post(url, headers=headers, params=params)
    return response.json()

# Order senden + TP1/2/3 Limits
def send_binance_order(symbol, side, quantity, tp_levels=[]):
    url = "https://fapi.binance.com/fapi/v1/order"
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': int(time.time() * 1000)
    }
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    headers = { "X-MBX-APIKEY": API_KEY }
    response = requests.post(url, headers=headers, params=params)

    tp_results = []

    if tp_levels:
        price = get_price(symbol)
        if price:
            precision = get_symbol_precision(symbol)
            tp_shares = [0.3, 0.2, 0.15]

            for i, tp in enumerate(tp_levels):
                if i >= len(tp_shares):
                    break
                tp_price = price * (1 + tp) if side == 'BUY' else price * (1 - tp)
                tp_price_rounded = round(tp_price, precision)
                qty = round(quantity * tp_shares[i], 6)

                params_tp = {
                    'symbol': symbol,
                    'side': 'SELL' if side == 'BUY' else 'BUY',
                    'type': 'LIMIT',
                    'quantity': qty,
                    'price': tp_price_rounded,
                    'timeInForce': 'GTC',
                    'timestamp': int(time.time() * 1000)
                }
                query_string_tp = urllib.parse.urlencode(params_tp)
                signature_tp = hmac.new(API_SECRET.encode(), query_string_tp.encode(), hashlib.sha256).hexdigest()
                params_tp['signature'] = signature_tp
                tp_response = requests.post(url, headers=headers, params=params_tp)
                tp_results.append(tp_response.json())

    return response.json(), tp_results

# Webhook-Route
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print("Webhook empfangen:", data)

        symbol = data.get('symbol', 'BTCUSDT')
        side = data.get('side')
        volume_usd = float(data.get('volume', 20))
        leverage = data.get('leverage')

        # Take Profit Level in Prozent (z. B. 2.0 = 2 %)
        tp1 = float(data.get('tp1', 2.0)) / 100
        tp2 = float(data.get('tp2', 8.0)) / 100
        tp3 = float(data.get('tp3', 18.0)) / 100
        tp_levels = [tp1, tp2, tp3]

        if not all([side, volume_usd]):
            return jsonify({'status': 'error', 'message': 'Fehlende Parameter'}), 400

        quantity = calculate_quantity(volume_usd, symbol)
        if quantity is None:
            return jsonify({'status': 'error', 'message': 'Ungültige Menge oder Preis nicht verfügbar'}), 400

        if leverage:
            leverage_response = set_leverage(symbol, leverage)
            print("Hebelantwort:", leverage_response)

        result, tp_results = send_binance_order(symbol, side.upper(), quantity, tp_levels)
        return jsonify({'status': 'Order gesendet', 'binance_response': result, 'tp_results': tp_results}), 200

    except Exception as e:
        print("Fehler im Webhook:", str(e))
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)



