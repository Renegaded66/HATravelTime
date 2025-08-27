from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

@app.route("/reisezeit", methods=["POST"])
def reisezeit():
    try:
        data = request.get_json()
        start = data.get("start")
        end = data.get("end")

        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://maps.google.com/maps/dir/{start}/{end}")

            # hier wie gehabt Cookie-Banner etc. abfangen …

            page.wait_for_timeout(5000)
            html = page.inner_html("#section-directions-trip-0")

            fahrtzeit = html.split("</div>")[0].split("Fk3sm")[1].split('">')[1]
            if "&nbsp;h" in fahrtzeit:
                stunden = int(fahrtzeit.split("&nbsp;h")[0].strip())
                minuten = int(fahrtzeit.split("&nbsp;h")[1].strip().split(" ")[0])
                fahrtzeit = stunden * 60 + minuten
            else:
                fahrtzeit = int(fahrtzeit.strip().split(" ")[0].strip())

            return jsonify({"fahrtzeit": fahrtzeit})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
