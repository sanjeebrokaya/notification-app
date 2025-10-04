from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# --- Config: support both env var names (K8s uses LOGGER_URL) ---
LOGGER_URL = (
    os.environ.get("LOGGER_URL")
    or os.environ.get("LOGGER_SERVICE_URL")
    or "http://logger:8081"
)

# --- CORS for local testing / static file usage ---
@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/notify", methods=["OPTIONS"])
def cors_preflight():
    return ("", 204)

# --- Health ---
@app.route("/", methods=["GET"])
def root():
    return jsonify({"service": "gateway", "status": "ok"}), 200

# --- POST /notify -> forwards to logger /log ---
@app.route("/notify", methods=["POST"])
def handle_notification():
    """Accepts JSON: { "message": "..." } and forwards to logger service."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"status": "error",
                        "message": "Provide JSON body with a non-empty 'message' field."}), 400

    try:
        resp = requests.post(f"{LOGGER_URL}/log",
                             json={"message": message}, timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        app.logger.exception("Failed to reach logger service")
        return jsonify({"status": "error",
                        "message": "Logger service unreachable",
                        "details": str(e)}), 502

    return jsonify({"status": "ok", "logged": resp.json()}), 200

# --- NEW: GET /logs -> proxies to logger /logs ---
@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        resp = requests.get(f"{LOGGER_URL}/logs", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as e:
        app.logger.exception("Failed to reach logger service for /logs")
        return jsonify({"status": "error",
                        "message": "Logger service unreachable",
                        "details": str(e)}), 502
    # Ensure JSON pass-through
    return jsonify(resp.json()), 200


if __name__ == "__main__":
    # Run in container
    app.run(host="0.0.0.0", port=8080)
