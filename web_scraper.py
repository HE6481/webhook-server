import urllib.request

# URL, von der der HTML-Inhalt abgerufen wird
url = 'https://www.example.com'

# HTML-Inhalt abrufen
response = urllib.request.urlopen(url)
html = response.read()

# HTML-Inhalt in eine Datei schreiben
with open('example.html', 'wb') as f:
    f.write(html)

print("Die HTML-Datei wurde erfolgreich gespeichert.")
