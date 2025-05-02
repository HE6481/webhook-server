import requests
import json

# Die URL des Webhooks (lokal auf deinem PC)
url = "http://127.0.0.1:5000/webhook"

# Die Daten, die du an den Webhook senden möchtest
data = {
    "message": "Hallo, Webhook!"
}

# Sende die POST-Anfrage
response = requests.post(url, json=data)

# Ausgabe der Server-Antwort
print(response.json())
