from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import nest_asyncio
import re
import urllib.parse

# nest_asyncio anwenden, um Event-Loop-Konflikte zu vermeiden
nest_asyncio.apply()

app = Flask(__name__)

COOKIE_BUTTON_TEXTS = re.compile(
    r"Alle ablehnen|Reject all|Alles ablehnen|Accept all|Alle akzeptieren",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(
    r"(?:(\d+)\s*(?:Std\.?|Stunden?|h)\s*)?(\d+)\s*min\b",
    re.IGNORECASE,
)
DISTANCE_PATTERN = re.compile(r"\b\d+(?:[,.]\d+)?\s*km\b", re.IGNORECASE)


def duration_to_minutes(text: str) -> int | None:
    """Extrahiert eine Dauer wie '27 min' oder '2 h 31 min' als Minuten."""
    match = DURATION_PATTERN.search(text.replace("\xa0", " "))
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    return hours * 60 + minutes


def get_best_route_text(page) -> str:
    """
    Liefert den Text der ersten Auto-Route in Google Maps.

    Google Maps hat die alten stabilen IDs wie #section-directions-trip-0
    entfernt. Aktuell stehen die Routen als sichtbare Cards im Routenplaner
    mit role=link/button. Eine Auto-Route enthält Dauer + Entfernung, während
    die Transportmodus-Leiste oben nur die Dauer enthält.
    """
    selectors = [
        # Aktuelles Google-Maps-Markup: einzelne Routenkarten
        'div[role="main"] div[role="link"]',
        'div[role="main"] div[role="button"]',
        # Fallback, falls Google die role-Attribute wieder ändert
        'div[role="main"] div',
    ]

    for selector in selectors:
        elements = page.locator(selector).all()
        for element in elements:
            try:
                if not element.is_visible():
                    continue
                text = element.inner_text(timeout=1000).replace("\xa0", " ").strip()
            except Exception:
                continue

            if DURATION_PATTERN.search(text) and DISTANCE_PATTERN.search(text):
                return text

    # Letzter Fallback: gesamten Routenplanertext scannen
    planner_text = page.locator('div[role="main"]').inner_text(timeout=5000).replace("\xa0", " ")
    if DURATION_PATTERN.search(planner_text):
        return planner_text

    raise ValueError("Keine Reisezeit im Google-Maps-Routenplaner gefunden.")


def get_travel_time(start: str, end: str) -> int:
    """
    Diese Funktion startet Playwright, navigiert zu Google Maps
    und extrahiert die Reisezeit.
    """
    print("Got request")
    browser = None
    try:
        with sync_playwright() as p:
            # Firefox bleibt Standard für das Home-Assistant-Add-on.
            browser = p.firefox.launch(headless=True)
            page = browser.new_page(locale="de-DE", timezone_id="Europe/Berlin")

            url = (
                "https://www.google.com/maps/dir/"
                f"{urllib.parse.quote(start, safe='')}/"
                f"{urllib.parse.quote(end, safe='')}"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            # Auf Cookie-Banner warten und ablehnen/akzeptieren, falls vorhanden.
            try:
                page.get_by_role("button", name=COOKIE_BUTTON_TEXTS).first.click(timeout=5000)
            except Exception:
                pass

            # Auf den aktuellen Routenplaner warten. Die frühere ID
            # #section-directions-trip-0 existiert derzeit nicht mehr.
            page.wait_for_selector('div[role="main"]', timeout=30000)
            page.wait_for_timeout(2000)

            route_text = get_best_route_text(page)
            travel_time = duration_to_minutes(route_text)
            if travel_time is None:
                raise ValueError(f"Reisezeit konnte nicht ausgelesen werden: {route_text!r}")

            browser.close()
            return travel_time

    except Exception as e:
        if browser is not None and browser.is_connected():
            browser.close()
        print("Fehler in get_travel_time:", e)
        import traceback
        traceback.print_exc()
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
    serve(app, host="0.0.0.0", port=6730)
