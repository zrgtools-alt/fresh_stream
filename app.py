import time
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError

app = Flask(__name__)

# ✅ Only FREE / PUBLIC channels
CHANNELS = {
    "green-entertainment": "https://tamashaweb.com/live/green-entertainment",
    "ary-news": "https://tamashaweb.com/live/ary-news",
}

PLAYWRIGHT_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
]

def fetch_fresh_m3u8(page_url: str) -> str | None:
    found_urls = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=PLAYWRIGHT_ARGS
        )
        context = browser.new_context()
        page = context.new_page()

        # 🔥 Capture ALL responses
        def on_response(response):
            try:
                url = response.url
                if ".m3u8" in url and "wmsAuthSign" in url:
                    print("FOUND HLS:", url)
                    found_urls.append(url)
            except Exception:
                pass

        page.on("response", on_response)

        try:
            print("Opening page:", page_url)
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)

            # ⏳ Tamasha HLS delay
            print("Waiting for HLS requests...")
            time.sleep(15)

        except TimeoutError:
            print("Page load timeout")
        finally:
            browser.close()

    # Return latest signed URL
    return found_urls[-1] if found_urls else None


@app.route("/", methods=["GET", "HEAD"])
def home():
    return {
        "status": "ok",
        "service": "fresh-stream-api",
        "usage": "/api/fresh_stream?channel=ary-news"
    }


@app.route("/api/fresh_stream", methods=["GET"])
def api_fresh_stream():
    channel = request.args.get("channel", "").strip().lower()

    if channel not in CHANNELS:
        return jsonify({
            "success": False,
            "error": "Unknown or unsupported channel"
        }), 404

    try:
        stream_url = fetch_fresh_m3u8(CHANNELS[channel])
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Internal error",
            "details": str(e)
        }), 500

    if not stream_url:
        return jsonify({
            "success": False,
            "error": "No active HLS stream found (maybe offline)"
        }), 404

    return jsonify({
        "success": True,
        "channel": channel,
        "stream_url": stream_url,
        "note": "Signed URL usually expires in ~10–30 minutes"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
