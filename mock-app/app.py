import hmac
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not set")


@app.route("/api/data", methods=["GET"])
def get_data():
    key = request.headers.get("x-api-key")

    if not key or not hmac.compare_digest(key, API_KEY):
        return jsonify({"error": "Unauthorized"}), 401

    return jsonify({"message": "Sensitive data accessed successfully!"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)