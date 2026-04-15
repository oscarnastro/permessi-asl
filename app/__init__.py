import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["OUTPUT_DIR"] = os.environ.get("OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "output"))
    os.makedirs(app.config["OUTPUT_DIR"], exist_ok=True)
    from .routes import bp
    app.register_blueprint(bp)
    return app
