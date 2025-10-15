from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import nest_asyncio

# nest_asyncio anwenden, um Event-Loop-Konflikte zu vermeiden
nest_asyncio.apply()

app = Flask(__name__)

def get_travel_time(start: str, end: str) -> int:
    """
    Diese Funktion startet Playwright, navigiert zu Google Maps
    und extrahiert die Reisezeit.
    """
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            
            # URL-Format angepasst, um korrekte Navigation zu gewährleisten
            url = f"https://www.google.com/maps/dir/{start}/{end}"
            page.goto(url)

            # Auf Cookie-Banner warten und ablehnen
            try:
                reject_button = page.locator('button:has-text("Alle ablehnen")').first
                reject_button.wait_for(timeout=5000) # 5 Sekunden warten
                reject_button.click()
            except Exception as e:
                print("Error")

            # Auf das Element mit der Reisezeit warten
            # Der Selektor zielt auf das erste prominente div mit der Zeitangabe
            trip_selector = "div#section-directions-trip-0"
            page.wait_for_selector(trip_selector, timeout=15000)
            
            # HTML-Inhalt des relevanten Abschnitts extrahieren
            html = page.inner_html(trip_selector)
            
            # Reisezeit extrahieren (deine Logik, leicht angepasst für Robustheit)
            # Sucht nach einem Div, das "h" oder "min" enthält
            time_str_part = html.split('</div>')[0].split('">')[-1]
            
            
            fahrtzeit_minuten = 0
            if "h" in time_str_part:
                parts = time_str_part.replace('h', '').replace('min', '').split()
                fahrtzeit_minuten = int(parts[0]) * 60 + int(parts[1])
            else:
                fahrtzeit_minuten = int(time_str_part.replace('min', '').strip())
                
            browser.close()
            return fahrtzeit_minuten

    except Exception as e:
        # Browser im Fehlerfall schließen
        if 'browser' in locals() and browser.is_connected():
            browser.close()
        return -1

@app.route('/traveltime', methods=['GET'])
def travel_time_endpoint():
    """
    API-Endpunkt, der start und end als Query-Parameter erwartet.
    Beispiel: /traveltime?start=Berlin&end=Hamburg
    """
    start_location = request.args.get('start')
    end_location = request.args.get('end')

    if not start_location or not end_location:
        return jsonify({"error": "Bitte 'start' und 'end' als Parameter angeben."}), 400

    travel_time = get_travel_time(start_location, end_location)

    if travel_time != -1:
        return jsonify({"travel_time_minutes": travel_time})
    else:
        return jsonify({"error": "Reisezeit konnte nicht ermittelt werden."}), 500

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8000)
