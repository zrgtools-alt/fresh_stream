import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright

app = Flask(__name__)

CHANNELS = {
    "ary-news": "https://tamashaweb.com/live/ary-news",
    "green-entertainment": "https://tamashaweb.com/live/green-entertainment",
}

ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

def fetch_fresh_m3u8(url):
    found = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=ARGS)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            viewport={"width": 1280, "height": 720},
        )
        page = ctx.new_page()

        # 🔥 Capture BOTH responses + requests
        def sniff(u):
            if ".m3u8" in u and "wmsAuthSign" in u:
                print("FOUND HLS:", u)
                found.append(u)

        page.on("response", lambda r: sniff(r.url))
        page.on("request", lambda r: sniff(r.url))

        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)

        # 🔥 Handle iframe player
        try:
            frame = page.frame_locator("iframe").first
            frame.locator("video").evaluate(
                """v => {
                    v.muted = true;
                    v.play();
                }"""
            )
        except:
            pass

        # 🔥 Fallback: force JS play on any video
        try:
            page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    if (v) {
                        v.muted = true;
                        v.play();
                    }
                }
            """)
        except:
            pass

        # ⏳ wait for HLS
        time.sleep(25)
        browser.close()

    return found[-1] if found else None


@app.route("/", methods=["GET", "HEAD"])
def home():
    return {
        "status": "ok",
        "service": "fresh-stream-api",
        "usage": "/api/fresh_stream?channel=ary-news"
    }


@app.route("/api/fresh_stream")
def api():
    channel = request.args.get("channel", "").lower()
    if channel not in CHANNELS:
        return {"success": False, "error": "invalid channel"}, 404

    stream = fetch_fresh_m3u8(CHANNELS[channel])
    if not stream:
        return {"success": False, "error": "No active HLS stream found"}, 404

    return {
        "success": True,
        "channel": channel,
        "stream_url": stream,
        "note": "Signed URL expires in ~10–30 minutes"
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
