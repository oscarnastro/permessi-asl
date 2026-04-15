import os
from flask import Flask
from dotenv import load_dotenv

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder=os.path.join(_BASE_DIR, "templates"), static_folder=os.path.join(_BASE_DIR, "static"))
    app.config["OUTPUT_DIR"] = os.environ.get("OUTPUT_DIR", os.path.join(_BASE_DIR, "output"))
    os.makedirs(app.config["OUTPUT_DIR"], exist_ok=True)
    from .routes import bp
    app.register_blueprint(bp)
    return app
