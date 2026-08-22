import os
import requests
from daten_einlesen import hole_forecast_daten

daten = hole_forecast_daten()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

for punkt in daten:
    if punkt["wind_ms"] > 3:

        nachricht = (
            "pack die badehose ein:\n"
            f"🚨 Wind-Alarm!\n"
            f"Zeit: {punkt['zeit']}\n"
            f"Wind: {punkt['wind_ms']} m/s\n"
            f"Böen: {punkt['boeen_ms']} m/s\n"
            f"Richtung: {punkt['richtung_grad']}°\n"
            f"Temperatur: {punkt['temp_kelvin']} K"
        )

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        antwort = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "text": nachricht
            }
        )

        print("Telegram:", antwort.status_code, antwort.text)