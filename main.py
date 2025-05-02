from flask import Flask, request, jsonify

app = Flask(__name__)

# NEU HINZUGEFÜGT:
@app.route('/')
def home():
    return 'Server läuft!'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    print("Webhook empfangen:", data)
    return jsonify({'status': 'erhalten'}), 200

if __name__ == '__main__':
    app.run(debug=True)

