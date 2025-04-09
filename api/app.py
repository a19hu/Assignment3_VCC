from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info("app_info", "App Info, this can be anything you want", version="1.0.0")

APP_NAME = os.getenv("APP_NAME", "Local vm")  # Default value if APP_NAME is not set


@app.route('/')
def home():
    return f"Hello from {APP_NAME}!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)