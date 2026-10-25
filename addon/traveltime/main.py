"""Travel Time add-on - scrapes Google Maps for a travel time.

Endpoint:
    GET /traveltime?start=<address|lat,lon>&end=<address|lat,lon>
        -> {"travel_time_minutes": 16, "distance_km": 12.4, "distance_text": "12,4 km"}
    GET /health
        -> {"status": "ok", "version": "..."}
"""

from flask import Flask, jsonify, request
import re
import urllib.parse

VERSION = "1.1.0"

app = Flask(__name__)

COOKIE_BUTTON_TEXTS = re.compile(
    r"Alle ablehnen|Reject all|Alles ablehnen|Accept all|Alle akzeptieren",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(
    r"(?:(\d+)\s*(?:Std\.?|Stunden?|h)\s*)?(\d+)\s*min\b",
    re.IGNORECASE,
)
DISTANCE_PATTERN = re.compile(r"\b\d+(?:[,.]\d+)?\s*(?:km|m)\b", re.IGNORECASE)
DISTANCE_VALUE_PATTERN = re.compile(r"(\d+(?:[,.]\d+)?)\s*(km|m)\b", re.IGNORECASE)

MAPS_URL = "https://www.google.com/maps/dir/{start}/{end}"


def duration_to_minutes(text: str) -> int | None:
    """Extrahiert eine Dauer wie '27 min' oder '2 h 31 min' als Minuten."""
    match = DURATION_PATTERN.search(text.replace("\xa0", " "))
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    return hours * 60 + minutes


def distance_to_km(text: str) -> float | None:
    """Extrahiert die erste Entfernung ('12,4 km' oder '800 m') in Kilometern."""
    match = DISTANCE_VALUE_PATTERN.search(text.replace("\xa0", " "))
    if not match:
        return None

    value = float(match.group(1).replace(",", "."))
    if match.group(2).lower() == "m":
        value /= 1000
    return round(value, 2)


def build_maps_url(start: str, end: str) -> str:
    """Baut die Routenplaner-URL.

    Start/Ziel dürfen Adressen oder bereits aufgelöste Koordinaten ("51.5,7.4") sein;
    Kommas bleiben lesbar, alles andere wird kodiert.
    """
    return MAPS_URL.format(
        start=urllib.parse.quote(start.strip(), safe=","),
        end=urllib.parse.quote(end.strip(), safe=","),
    )


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


def get_travel_time(start: str, end: str) -> dict:
    """
    Startet Playwright, navigiert zu Google Maps und extrahiert die Reisezeit.

    Rückgabe bei Erfolg: {"travel_time_minutes": int, "distance_km": float|None, ...}
    Rückgabe bei Fehler:  {"error": "<Meldung>"}
    """
    # Playwright wird erst hier importiert: so bleiben die Parser-Funktionen
    # ohne Browser-Abhängigkeit testbar.
    from playwright.sync_api import sync_playwright

    print(f"Got request: {start!r} -> {end!r}", flush=True)
    browser = None
    try:
        with sync_playwright() as p:
            # Firefox bleibt Standard für das Home-Assistant-Add-on.
            browser = p.firefox.launch(headless=True)
            page = browser.new_page(locale="de-DE", timezone_id="Europe/Berlin")

            page.goto(build_maps_url(start, end), wait_until="domcontentloaded", timeout=60000)

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
            browser = None

            return {
                "travel_time_minutes": travel_time,
                "distance_km": distance_to_km(route_text),
                "distance_text": _first_distance_text(route_text),
                "version": VERSION,
            }

    except Exception as e:
        print("Fehler in get_travel_time:", e, flush=True)
        import traceback

        traceback.print_exc()
        return {"error": f"{type(e).__name__}: {e}"}
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:  # noqa: BLE001 - Browser kann bereits weg sein
                pass


def _first_distance_text(text: str) -> str | None:
    """Gibt die erste gefundene Entfernungsangabe im Original zurück (z. B. '12,4 km')."""
    match = DISTANCE_VALUE_PATTERN.search(text.replace("\xa0", " "))
    return match.group(0).strip() if match else None


@app.route("/health", methods=["GET"])
def health():
    """Wird von der Integration als schneller Erreichbarkeitscheck genutzt."""
    return jsonify({"status": "ok", "version": VERSION})


@app.route("/traveltime", methods=["GET"])
def travel_time_endpoint():
    """
    API-Endpunkt, der start und end als Query-Parameter erwartet.
    Beispiel: /traveltime?start=Berlin&end=Hamburg
    """
    start_location = (request.args.get("start") or "").strip()
    end_location = (request.args.get("end") or "").strip()

    if not start_location or not end_location:
        return jsonify({"error": "Bitte 'start' und 'end' als Parameter angeben."}), 400

    result = get_travel_time(start_location, end_location)

    if "error" in result:
        return jsonify(result), 500
    return jsonify(result)


if __name__ == "__main__":
    from waitress import serve

    serve(app, host="0.0.0.0", port=6730)
