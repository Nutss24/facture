import time
import requests
import datetime
from zoneinfo import ZoneInfo
from flask import Flask
import threading
import requests as req_ping
import traceback

# ==== CONFIGURATION ====

WEBHOOK_URL = "https://discord.com/api/webhooks/1378351740075642920/0KiVgc5upTWzNOVX1NoEcfrQ-PiV0q_mjscPLOaFyZ1JhvysqC0SizYdK1hlwLKPSXAK"
API_URL = "https://api.glife.fr/roleplay/org/invoices?id=1397"
REFRESH_INTERVAL = 10  # Vérification des factures toutes les 5 minutes
PING_INTERVAL = 3600    # Ping de vie toutes les heures
AUTO_PING_URL = "https://facture-urjb.onrender.com"

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

totaux_clients = {}
total_general = 0

def envoyer_discord(message):
    payload = {"content": message}
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code != 204:
            print(f"Erreur Discord : {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erreur d'envoi Discord : {e}")

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
                montant = facture.get("revenue", 0)
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
    try:
        envoyer_discord("✅ Le script est actif et surveille les factures !")
        last_timestamp = get_timestamp_now()
        while True:
            time.sleep(REFRESH_INTERVAL)
            current_timestamp = get_timestamp_now()
            print(f"🔎 Vérification entre {last_timestamp} et {current_timestamp}...")
            check_factures(last_timestamp, current_timestamp)
            last_timestamp = current_timestamp
    except Exception as e:
        erreur = traceback.format_exc()
        envoyer_discord(f"❌ Attention ! Le script a rencontré une erreur :\n```{erreur}```")

def auto_ping():
    while True:
        try:
            print("🔄 Auto-ping envoyé...")
            req_ping.get(AUTO_PING_URL)
        except Exception as e:
            print("Erreur lors de l'auto-ping :", e)
        time.sleep(300)  # Ping toutes les 5 minutes

def ping_discord():
    while True:
        try:
            maintenant = datetime.datetime.now(tz=ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d %H:%M:%S")
            envoyer_discord(f"✅ Le script est toujours actif à {maintenant}.")
        except Exception as e:
            print("Erreur lors du ping Discord :", e)
        time.sleep(PING_INTERVAL)  # Ping toutes les heures

# Lancer les threads
threading.Thread(target=boucle).start()
threading.Thread(target=auto_ping).start()
threading.Thread(target=ping_discord).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
