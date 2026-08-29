import os
import requests
from collections import defaultdict
from daten_einlesen import hole_forecast_daten

daten = hole_forecast_daten()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

START_STUNDE = 11
END_STUNDE = 17
MIN_WIND_KN = 15

# 1. Nach Tag gruppieren, dabei nur Zeitslots im relevanten Fenster behalten
nach_tag = defaultdict(list)
for punkt in daten:
    stunde = int(punkt["zeit"][11:13])
    if START_STUNDE <= stunde <= END_STUNDE:
        tag = punkt["zeit"][:10]
        nach_tag[tag].append(punkt)

# 2. Für jeden Tag prüfen, ob ALLE Zeitslots im Fenster über MIN_WIND_KN liegen
for tag, punkte_am_tag in nach_tag.items():
    if not punkte_am_tag:
        continue
    if all(p["wind_kn"] > MIN_WIND_KN for p in punkte_am_tag):
        zeilen = "\n".join(
            f"  {p['zeit'][11:16]} Uhr: {p['wind_kn']} kn (Böen {p['boeen_kn']} kn), "
            f"{p['richtung_grad']}°, {p['temp_celsius']} °C"
            for p in punkte_am_tag
        )
        nachricht = (
            "pack die badehose ein:\n"
            f"🚨 Wind-Alarm für {tag}! Durchgängig über {MIN_WIND_KN} kn ({START_STUNDE}-{END_STUNDE} Uhr):\n"
            f"{zeilen}"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        antwort = requests.post(
            url,
            data={"chat_id": CHAT_ID, "text": nachricht}
        )
        print("Telegram:", antwort.status_code, antwort.text)
