from pathlib import Path

from dotenv import load_dotenv

from flask_app.app import create_app
from flask_app.db.engine import init_db

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

init_db()
app = create_app()
app.run(host="0.0.0.0", port=5000)