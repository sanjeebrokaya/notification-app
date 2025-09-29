from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# naive CORS for local testing
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return resp

@app.route('/notify', methods=['OPTIONS'])
def cors_preflight():
    return ('', 204)


LOGGER_SERVICE_URL = os.environ.get("LOGGER_SERVICE_URL", "http://logger:8081")

@app.route("/", methods=["GET"])
def root():
    return jsonify({"service": "gateway", "status": "ok"}), 200

@app.route("/notify", methods=["POST"])
def handle_notification():
    """Accepts JSON: { "message": "..." } and forwards to logger service."""
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    if not message or not isinstance(message, str):
        return jsonify({"status": "error", "message": "Provide JSON body with a non-empty 'message' field."}), 400

    try:
        resp = requests.post(f"{LOGGER_SERVICE_URL}/log", json={"message": message}, timeout=5)
    except requests.RequestException as e:
        app.logger.exception("Failed to reach logger service")
        return jsonify({"status": "error", "message": "Logger service unreachable", "details": str(e)}), 502

    if resp.status_code == 200:
        payload = resp.json()
        return jsonify({"status": "ok", "logged": payload}), 200
    else:
        return jsonify({"status": "error", "message": "Logger service error", "details": resp.text}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
