import time
import requests
import datetime
from zoneinfo import ZoneInfo
from flask import Flask
import threading
import requests as req_ping

# ==== CONFIGURATION ====

WEBHOOK_URL = "https://discord.com/api/webhooks/1378351740075642920/0KiVgc5upTWzNOVX1NoEcfrQ-PiV0q_mjscPLOaFyZ1JhvysqC0SizYdK1hlwLKPSXAK"
API_URL = "https://apirp.glife.fr/roleplay/org/invoices?id=1397&characterId=239519"
REFRESH_INTERVAL = 300  # Vérification toutes les 5 minutes
AUTO_PING_URL = "https://facture-urjb.onrender.com"  # Mets ici l'URL de ton Render

# ========================

# Flask app pour Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Le script tourne bien ✅", 200

@app.route("/totaux")
def afficher_totaux():
    global totaux_clients, total_general
    if not totaux_clients:
        return "Aucune donnée disponible pour le moment."
    message = "📊 Totaux par client :\n"
    for client, total in totaux_clients.items():
        message += f"- {client} : {total} 💼\n"
    message += f"\n💰 Total général : {total_general}"
    return f"<pre>{message}</pre>", 200

@app.route("/reset")
def reset_totaux():
    global totaux_clients, total_general
    totaux_clients = {}
    total_general = 0
    return "Totaux remis à zéro ✅", 200

# Dictionnaire pour stocker les totaux par client
totaux_clients = {}
# Variable pour le total général
total_general = 0

def envoyer_discord(message):
    payload = {"content": message}
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code != 204:
        print(f"Erreur Discord : {response.status_code} - {response.text}")

def get_timestamp_now():
    return int(time.time())

def check_factures(start, end):
    global total_general
    url = f"{API_URL}&start={start}&end={end}"
    response = requests.get(url, headers={"accept": "application/json"})
    if response.status_code == 200:
        data = response.json()
        if data:
            print("Réponse API brute : ", data)
            for facture in data:
                facture_id = facture.get("id", "Inconnu")
                montant = facture.get("revenue", 0)  # Adapter le champ ici (ex : "revenue")
                try:
                    montant = int(montant)
                except:
                    montant = 0
                nom = facture.get("name", f"ID inconnu ({facture_id})")
                totaux_clients[nom] = totaux_clients.get(nom, 0) + montant
                total_general += montant
                date_facture = datetime.datetime.fromtimestamp(
                    facture.get("timestamp", start),
                    tz=ZoneInfo("Europe/Paris")
                ).strftime('%Y-%m-%d %H:%M:%S')
                message = f"""📄 Nouvelle facture détectée :
- Client : {nom}
- Montant : {montant} 💵
- Date : {date_facture}
- Total facturé par {nom} : {totaux_clients[nom]} 💼
- Total général : {total_general} 💰"""
                envoyer_discord(message)
            print(f"{len(data)} nouvelle(s) facture(s) trouvée(s).")
        else:
            print("Aucune nouvelle facture trouvée.")
    else:
        print(f"Erreur API : {response.status_code} - {response.text}")

def boucle():
    print("🚀 Surveillance des factures en cours...")
    last_timestamp = get_timestamp_now()
    while True:
        time.sleep(REFRESH_INTERVAL)
        current_timestamp = get_timestamp_now()
        print(f"🔎 Vérification entre {last_timestamp} et {current_timestamp}...")
        check_factures(last_timestamp, current_timestamp)
        last_timestamp = current_timestamp

def auto_ping():
    while True:
        try:
            print("🔄 Auto-ping envoyé...")
            req_ping.get(AUTO_PING_URL)
        except Exception as e:
            print("Erreur lors de l'auto-ping :", e)
        time.sleep(300)  # Ping toutes les 5 minutes

# Lancer les threads
threading.Thread(target=boucle).start()
threading.Thread(target=auto_ping).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
