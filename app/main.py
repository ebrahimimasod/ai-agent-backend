from flask import Flask, jsonify
from flask_cors import CORS
from app.core.config import settings
from app.db.session import engine
from app.db.models import Base
from app.api.routes_ingest import ingest_bp
from app.api.routes_posts import posts_bp
from app.api.routes_chat import chat_bp

app = Flask(__name__)
CORS(app)

# Auto-create tables for MVP
Base.metadata.create_all(bind=engine)

app.register_blueprint(ingest_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(chat_bp)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})
