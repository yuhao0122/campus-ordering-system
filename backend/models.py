import sqlite3
from collections import OrderedDict
from pathlib import Path

from flask import current_app, g

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE = REPO_ROOT / "instance" / "campus_ordering.db"


class DomainError(Exception):
    """An expected validation or ownership failure safe to show to users."""


def get_db():
    if "db" not in g:
        database = Path(current_app.config.get("DATABASE", DEFAULT_DATABASE))
        database.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(database, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    existing = {row[1] for row in db.execute("PRAGMA table_info(products)")}
    if existing and "merchant_id" not in existing:
        raise RuntimeError("偵測到舊版資料庫；請先執行 flask --app app migrate-db。")
    db.executescript(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))


def migrate_legacy_db():
    db = get_db()
    columns = {row[1] for row in db.execute("PRAGMA table_info(products)")}
    if not columns or "merchant_id" in columns:
        init_db()
        return False
    db.execute("PRAGMA foreign_keys = OFF")
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("ALTER TABLE products RENAME TO legacy_products")
        if _table_exists(db, "order_items"):
            db.execute("ALTER TABLE order_items RENAME TO legacy_order_items")
        if _table_exists(db, "orders"):
            db.execute("ALTER TABLE orders RENAME TO legacy_orders")
        for statement in Path(__file__).with_name("schema.sql").read_text(encoding="utf-8").split(";"):
            if statement.strip():
                db.execute(statement)
        merchant_id = db.execute("INSERT INTO merchants(name) VALUES (?)", ("校園食堂",)).lastrowid
        db.execute(
            "INSERT INTO products(id, merchant_id, name, price) SELECT id, ?, name, price FROM legacy_products",
            (merchant_id,),
        )
        if _table_exists(db, "legacy_orders"):
            db.execute(
                "INSERT INTO orders(id, session_token, merchant_id, total_amount, payment_status, created_at) "
                "SELECT id, 'legacy', ?, total_amount, payment_status, created_at FROM legacy_orders",
                (merchant_id,),
            )
        if _table_exists(db, "legacy_order_items"):
            db.execute(
                "INSERT INTO order_items(id, order_id, product_id, product_name, quantity, unit_price) "
                "SELECT oi.id, oi.order_id, oi.product_id, p.name, oi.quantity, oi.unit_price "
                "FROM legacy_order_items oi JOIN legacy_products p ON p.id = oi.product_id"
            )
        for table in ("legacy_order_items", "legacy_orders", "legacy_products"):
            if _table_exists(db, table):
                db.execute(f"DROP TABLE {table}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.execute("PRAGMA foreign_keys = ON")
    return True


def _table_exists(db, name):
    return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def list_merchants():
    return [dict(row) for row in get_db().execute("SELECT id, name FROM merchants ORDER BY id")]


def list_products():
    rows = get_db().execute(
        "SELECT p.id, p.merchant_id, m.name merchant_name, p.name, p.description, p.price, "
        "p.image_url, p.is_available FROM products p JOIN merchants m ON m.id=p.merchant_id ORDER BY p.id"
    )
    return [_product_dict(row) for row in rows]


def list_products_by_merchant(merchant_id):
    rows = get_db().execute(
        "SELECT id, name, price, is_available FROM products WHERE merchant_id=? ORDER BY id", (merchant_id,)
    )
    return [{**dict(row), "is_available": bool(row["is_available"])} for row in rows]


def create_product(merchant_id, name, price):
    cursor = get_db().execute(
        "INSERT INTO products(merchant_id, name, price) VALUES (?, ?, ?)", (merchant_id, name, price)
    )
    return cursor.lastrowid


def _product_dict(row):
    value = dict(row)
    value["is_available"] = bool(value["is_available"])
    return value


def get_or_create_cart(session_token):
    db = get_db()
    db.execute("INSERT OR IGNORE INTO carts(session_token) VALUES (?)", (session_token,))
    return db.execute("SELECT id FROM carts WHERE session_token=?", (session_token,)).fetchone()["id"]


def add_cart_item(session_token, product_id, quantity):
    db = get_db()
    product = db.execute("SELECT id, is_available FROM products WHERE id=?", (product_id,)).fetchone()
    if product is None:
        raise DomainError("找不到指定商品。")
    if not product["is_available"]:
        raise DomainError("此商品已下架，無法加入購物車。")
    cart_id = get_or_create_cart(session_token)
    db.execute(
        "INSERT INTO cart_items(cart_id, product_id, quantity) VALUES (?, ?, ?) "
        "ON CONFLICT(cart_id, product_id) DO UPDATE SET quantity=quantity+excluded.quantity",
        (cart_id, product_id, quantity),
    )
    db.execute("UPDATE carts SET updated_at=CURRENT_TIMESTAMP WHERE id=?", (cart_id,))


def update_cart_item(session_token, product_id, quantity):
    db = get_db()
    item = db.execute(
        "SELECT p.is_available FROM cart_items ci JOIN carts c ON c.id=ci.cart_id "
        "JOIN products p ON p.id=ci.product_id WHERE c.session_token=? AND ci.product_id=?",
        (session_token, product_id),
    ).fetchone()
    if item is None:
        raise DomainError("購物車中沒有這項商品。")
    if not item["is_available"]:
        raise DomainError("此商品已下架，請從購物車移除。")
    cursor = db.execute(
        "UPDATE cart_items SET quantity=? WHERE product_id=? AND cart_id=(SELECT id FROM carts WHERE session_token=?)",
        (quantity, product_id, session_token),
    )
    if cursor.rowcount == 0:
        raise DomainError("購物車更新失敗。")


def remove_cart_item(session_token, product_id):
    cursor = get_db().execute(
        "DELETE FROM cart_items WHERE product_id=? AND cart_id=(SELECT id FROM carts WHERE session_token=?)",
        (product_id, session_token),
    )
    return cursor.rowcount > 0


def get_cart_groups(session_token):
    rows = get_db().execute(
        "SELECT p.merchant_id, m.name merchant_name, p.id product_id, p.name, p.price unit_price, ci.quantity "
        "FROM carts c JOIN cart_items ci ON ci.cart_id=c.id JOIN products p ON p.id=ci.product_id "
        "JOIN merchants m ON m.id=p.merchant_id WHERE c.session_token=? ORDER BY p.merchant_id, p.id",
        (session_token,),
    )
    groups = OrderedDict()
    total = 0
    for row in rows:
        subtotal = row["unit_price"] * row["quantity"]
        group = groups.setdefault(row["merchant_id"], {"merchant_id": row["merchant_id"], "merchant_name": row["merchant_name"], "items": [], "subtotal": 0})
        group["items"].append({"merchant_id": row["merchant_id"], "product_id": row["product_id"], "name": row["name"], "unit_price": row["unit_price"], "quantity": row["quantity"], "subtotal": subtotal})
        group["subtotal"] += subtotal
        total += subtotal
    return list(groups.values()), total


def create_orders_from_cart(session_token, idempotency_key):
    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        batch = db.execute("SELECT id FROM checkout_batches WHERE session_token=? AND idempotency_key=?", (session_token, idempotency_key)).fetchone()
        if batch:
            db.commit()
            return batch["id"], True
        rows = list(db.execute(
            "SELECT c.id cart_id, p.id product_id, p.merchant_id, p.name, p.price, p.is_available, ci.quantity "
            "FROM carts c JOIN cart_items ci ON ci.cart_id=c.id JOIN products p ON p.id=ci.product_id "
            "WHERE c.session_token=? ORDER BY p.merchant_id, p.id", (session_token,)
        ))
        if not rows:
            raise DomainError("購物車是空的，無法建立訂單。")
        if any(not row["is_available"] for row in rows):
            raise DomainError("購物車內有商品已下架，請移除後再結帳。")
        batch_id = db.execute("INSERT INTO checkout_batches(session_token,idempotency_key) VALUES (?,?)", (session_token,idempotency_key)).lastrowid
        groups = OrderedDict()
        for row in rows:
            groups.setdefault(row["merchant_id"], []).append(row)
        for merchant_id, items in groups.items():
            total = sum(item["price"] * item["quantity"] for item in items)
            order_id = db.execute(
                "INSERT INTO orders(session_token,merchant_id,checkout_batch_id,total_amount) VALUES (?,?,?,?)",
                (session_token, merchant_id, batch_id, total),
            ).lastrowid
            db.executemany(
                "INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price) VALUES (?,?,?,?,?)",
                [(order_id, item["product_id"], item["name"], item["quantity"], item["price"]) for item in items],
            )
        db.execute("DELETE FROM cart_items WHERE cart_id=?", (rows[0]["cart_id"],))
        db.commit()
        return batch_id, False
    except Exception:
        db.rollback()
        raise


def get_orders_by_batch(session_token, batch_id):
    return _load_orders("o.session_token=? AND o.checkout_batch_id=?", (session_token, batch_id))


def get_recent_orders(session_token):
    row = get_db().execute("SELECT id FROM checkout_batches WHERE session_token=? ORDER BY id DESC LIMIT 1", (session_token,)).fetchone()
    return get_orders_by_batch(session_token, row["id"]) if row else []


def list_orders_by_merchant(merchant_id):
    return _load_orders("o.merchant_id=?", (merchant_id,))


def list_orders():
    return _load_orders("1=1", ())


def _load_orders(where, params):
    db = get_db()
    rows = list(db.execute(
        "SELECT o.id order_id,o.merchant_id,m.name merchant_name,o.created_at,o.total_amount total,o.payment_status "
        "FROM orders o JOIN merchants m ON m.id=o.merchant_id WHERE " + where + " ORDER BY o.id DESC", params
    ))
    result = []
    for row in rows:
        order = dict(row)
        order["items"] = [{**dict(item), "subtotal": item["unit_price"] * item["quantity"]} for item in db.execute(
            "SELECT product_id,product_name name,unit_price,quantity FROM order_items WHERE order_id=? ORDER BY id", (row["order_id"],)
        )]
        result.append(order)
    return result


def pay_order(session_token, order_id):
    db = get_db()
    row = db.execute("SELECT payment_status FROM orders WHERE id=? AND session_token=?", (order_id, session_token)).fetchone()
    if row is None:
        raise DomainError("找不到可付款的訂單。")
    if row["payment_status"] == "paid":
        return False
    db.execute("UPDATE orders SET payment_status='paid' WHERE id=? AND session_token=? AND payment_status='unpaid'", (order_id, session_token))
    return True
