import requests
import re
import html
import json
from datetime import datetime, timedelta


def hole_html(url, speicherpfad="windfinder.html"):
    """Ruft die Seite ab, speichert sie lokal und gibt den HTML-Text zurück."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=20)
    with open(speicherpfad, "w", encoding="utf-8") as f:
        f.write(response.text)
    return response.text


def finde_forecast_data_init(html_text):
    """Findet das astro-island mit component-url 'ForecastDataInit' und gibt
    dessen props als Python-Dict zurück (enthält alle ~10 Tage Vorhersage)."""
    inseln = re.findall(
        r'<astro-island[^>]*component-url="([^"]*)"[^>]*props="([^"]*)"',
        html_text,
    )
    for component_url, props_escaped in inseln:
        if "ForecastDataInit" in component_url:
            props_json_text = html.unescape(props_escaped)
            return json.loads(props_json_text)
    return None


def extrahiere_forecast_liste(forecast_data_init):
    """Wandelt die verschachtelte fcSectionData-Struktur (mehrere Abschnitte
    mit je mehreren Tagen) in eine einfache, flache Liste von
    Vorhersage-Punkten um."""
    ergebnis = []
    sections = forecast_data_init["fcSectionData"][1]

    for section in sections:
        tage = section[1]
        for tag_eintrag in tage:
            tag_daten = tag_eintrag[1]
            horizons = tag_daten["horizons"][1]

            for horizon_eintrag in horizons:
                horizon_daten = horizon_eintrag[1]
                werte = horizon_daten["fcData"][1]

                punkt = {
                    "zeit": werte["dtl"][1],
                    "wind_ms": werte["ws"][1],
                    "boeen_ms": werte["wg"][1],
                    "richtung_grad": werte["wd"][1],
                    "temp_kelvin": werte["at"][1],
                }
                ergebnis.append(punkt)
      
    MS_ZU_KNOTEN = 1.943844
    KELVIN_ZU_CELSIUS = 273.15
    for eintrag in ergebnis:
        eintrag['wind_kn'] = round(eintrag.pop('wind_ms') * MS_ZU_KNOTEN, 1)
        eintrag['boeen_kn'] = round(eintrag.pop('boeen_ms') * MS_ZU_KNOTEN, 1)
        eintrag['temp_celsius'] = round(eintrag.pop('temp_kelvin') - KELVIN_ZU_CELSIUS, 1)

    return ergebnis


def ist_wochenende(zeit_text):
    """Prüft, ob ein ISO-Zeitstempel auf Samstag oder Sonntag fällt."""
    dt = datetime.fromisoformat(zeit_text)
    return dt.weekday() >= 5  # 5 = Samstag, 6 = Sonntag


def filtere_wochenende(forecast_liste):
    """Gibt nur die Vorhersage-Punkte zurück, die auf ein Wochenende fallen."""
    return [punkt for punkt in forecast_liste if ist_wochenende(punkt["zeit"])]


def filtere_naechste_tage(forecast_liste, anzahl_tage=5):
    """Gibt nur die Vorhersage-Punkte zurück, die innerhalb der naechsten
    'anzahl_tage' Tage ab jetzt liegen."""
    jetzt = datetime.now().astimezone()
    grenze = jetzt + timedelta(days=anzahl_tage)
    return [
        punkt for punkt in forecast_liste
        if jetzt <= datetime.fromisoformat(punkt["zeit"]) <= grenze
    ]


def filtere_uhrzeit(forecast_liste, start_stunde=11, end_stunde=20):
    """Gibt nur die Vorhersage-Punkte zurück, deren lokale Uhrzeit zwischen
    start_stunde und end_stunde (jeweils inklusive) liegt."""
    ergebnis = []
    for punkt in forecast_liste:
        stunde = datetime.fromisoformat(punkt["zeit"]).hour
        if start_stunde <= stunde <= end_stunde:
            ergebnis.append(punkt)
    return ergebnis


def speichere_als_json(daten, pfad="forecast_gefiltert.json"):
    """Speichert eine Liste von Vorhersage-Punkten als JSON-Datei."""
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)


def hole_forecast_daten(url="https://de.windfinder.com/forecast/loissin",
                         anzahl_tage=5, start_stunde=11, end_stunde=20):
    """Holt die Windfinder-Vorhersage und gibt die gefilterte Liste
    (naechste 'anzahl_tage' Tage, Uhrzeit zwischen start_stunde und
    end_stunde) als Python-Liste von Dicts zurueck. Diese Funktion kann
    von einem anderen Script importiert und direkt genutzt werden:

        from daten_einlesen import hole_forecast_daten
        daten = hole_forecast_daten()
    """
    html_text = hole_html(url)

    forecast_data_init = finde_forecast_data_init(html_text)
    if forecast_data_init is None:
        raise RuntimeError(
            "Konnte ForecastDataInit nicht finden - Seitenstruktur hat sich evtl. geändert."
        )

    forecast_liste = extrahiere_forecast_liste(forecast_data_init)
    naechste_tage = filtere_naechste_tage(forecast_liste, anzahl_tage=anzahl_tage)
    gefiltert = filtere_uhrzeit(naechste_tage, start_stunde=start_stunde, end_stunde=end_stunde)

    return gefiltert


def main():
    gefiltert = hole_forecast_daten()

    print(f"{len(gefiltert)} Vorhersage-Punkte nach Filterung gefunden:\n")
    for punkt in gefiltert:
        print(punkt)

    speichere_als_json(gefiltert, "forecast_gefiltert.json")
    print("\nGespeichert in forecast_gefiltert.json")


if __name__ == "__main__":
    main()