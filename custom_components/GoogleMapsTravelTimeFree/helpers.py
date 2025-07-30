import logging
from pathlib import Path
import subprocess
import sys

from playwright.sync_api import sync_playwright

_LOGGER = logging.getLogger(__name__)


def firefox_installed() -> bool:
    cache = Path.home() / ".cache" / "ms-playwright"
    # Je nach Version kann der Unterordner firefox-<version> sein
    return (
        any(d.name.startswith("firefox-") for d in cache.iterdir() if d.is_dir())
        if cache.exists()
        else False
    )


def ensure_firefox():
    if firefox_installed():
        return
    install_playwright_browsers()


def berechne_reisezeit(start: str, end: str) -> float:
    # ensure_firefox()
    # _LOGGER.info(str(str(start) + "," + str(end)))
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True, slow_mo=100)
            page = browser.new_page()
            page.goto(f"https://maps.google.com/maps/dir/{start}/{end}")

            # Warten, bis das Cookie-Zustimmungsbanner sichtbar ist
            page.wait_for_selector(
                'xpath=//button[contains(., "Alle ablehnen") or contains(., "Reject all") or contains(., "Rechazar todo") or contains(., "Tout refuser")]'
            )

            # Klicken auf den ersten gefundenen Button
            page.locator(
                'xpath=//button[contains(., "Alle ablehnen") or contains(., "Reject all") or contains(., "Rechazar todo") or contains(., "Tout refuser")]'
            ).first.click()

            # Warten, bis die Seite vollständig geladen ist
            page.wait_for_timeout(5000)
            html = page.inner_html("#section-directions-trip-0")
            # print(html)
            # fahrtzeit = html.split('<div class="Fk3sm fontHeadlineSmall delay-light">')[
            #    1
            # ]
            fahrtzeit = html.split("</div>")[0].split("Fk3sm")[1].split('">')[1]
            # print(fahrtzeit)
            fahrtzeit = fahrtzeit.split("</div>")[0]
            # print(fahrtzeit)
            if "&nbsp;h" in fahrtzeit:
                fahrtzeit = int(fahrtzeit.split("&nbsp;h")[0].strip()) * 60 + int(
                    fahrtzeit.split("&nbsp;h")[1].strip().split(" ")[0].strip()
                )
            else:
                fahrtzeit = int(fahrtzeit.strip().split(" ")[0].strip())
            # if fahrtzeit.isnmeric():
            return int(fahrtzeit)
    except Exception as e:
        # print(e)
        _LOGGER.info(f"Error while fetching Website Data: {e}")
        return -1


def install_playwright_browsers():
    try:
        # Sicherstellen, dass Playwright installiert ist
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])

        # Browser installieren
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install", "firefox"]
        )

        # Installiere Playwright-Browser mit Abhängigkeiten
        subprocess.check_call(
            [sys.executable, "-m", "playwright", "install-deps", "firefox"]
        )
        # _LOGGER.info("Firefox Browser und dependecies installiert.")

    except subprocess.CalledProcessError as e:
        print(f"Fehler bei der Installation von Playwright oder den Browsern: {e}")
        sys.exit(1)
