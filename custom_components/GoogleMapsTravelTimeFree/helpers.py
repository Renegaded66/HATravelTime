import logging
from pathlib import Path
import subprocess
import sys


_LOGGER = logging.getLogger(__name__)


import subprocess
import sys
from pathlib import Path


def ensure_playwright_installed():
    try:
        subprocess.check_call(["playwright", "--version"], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        _LOGGER.error("Playwright CLI not found.")
        return

    try:
        # Browser installieren, falls noch nicht installiert
        subprocess.check_call(["playwright", "install", "firefox"])
        _LOGGER.info("Successfully installed playwright browser.")
    except Exception as e:
        print(f"Exception: {e}")
        _LOGGER.error(f"Error while installing browser: {e}")


def berechne_reisezeit(start: str, end: str) -> float:
    ensure_playwright_installed()
    from playwright.sync_api import sync_playwright

    _LOGGER.info(str(str(start) + "," + str(end)))
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False, slow_mo=100)
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
        print(e)
        # _LOGGER.info(f"Error while fetching Website Data: {e}")
        return -1
