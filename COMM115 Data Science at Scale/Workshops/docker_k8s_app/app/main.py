import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Docker (v1)!"

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    # When running locally, default to port 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
