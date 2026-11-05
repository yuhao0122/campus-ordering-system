import sqlite3
from pathlib import Path
from flask import current_app, g

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = REPO_ROOT / "instance" / "campus_ordering.db"

def get_db():
    if "db" not in g:
        database = Path(current_app.config.get("DATABASE", DEFAULT_DATABASE))
        database.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None: db.close()

def init_db():
    db = get_db()
    db.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
    db.commit()

def list_products():
    return get_db().execute("SELECT id, name, price FROM products ORDER BY id").fetchall()

def create_product(name, price):
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"id": cursor.lastrowid, "name": name, "price": price}
