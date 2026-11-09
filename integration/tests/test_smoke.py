import sqlite3

import pytest

from backend.app import create_app
from backend.models import get_db, init_db
from backend.seed import seed_data


@pytest.fixture
def app(tmp_path):
    application = create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": str(tmp_path / "test.db")})
    with application.app_context():
        init_db()
        seed_data()
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def login_token(client, token="student-a", merchant_id=1):
    with client.session_transaction() as session:
        session["cart_token"] = token
        session["merchant_id"] = merchant_id


def add(client, product_id, quantity=1, follow=True):
    return client.post("/cart/add", data={"product_id": product_id, "quantity": quantity}, follow_redirects=follow)


def checkout_key(client):
    client.get("/checkout")
    with client.session_transaction() as session:
        return session["checkout_key"]


def test_health_schema_foreign_keys_and_idempotent_init(app, client):
    assert client.get("/health").get_json() == {"status": "ok"}
    with app.app_context():
        db = get_db()
        tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"merchants", "products", "carts", "cart_items", "checkout_batches", "orders", "order_items"} <= tables
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        before = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        init_db()
        assert db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == before


def test_seed_idempotent_and_menu_renders_data(app, client):
    with app.app_context():
        seed_data(); seed_data()
        assert get_db().execute("SELECT COUNT(*) FROM merchants").fetchone()[0] == 2
        assert get_db().execute("SELECT COUNT(*) FROM products").fetchone()[0] == 4
    page = client.get("/menu").get_data(as_text=True)
    assert "雞腿便當" in page and "NT$85" in page and "紅茶" in page


def test_add_accumulates_and_cart_context_is_complete(app, client):
    login_token(client)
    response = add(client, 1, 2)
    assert response.request.path == "/menu"
    assert "已加入購物車" in response.get_data(as_text=True)
    add(client, 1, 1)
    page = client.get("/cart").get_data(as_text=True)
    assert "雞腿便當" in page and 'value="3"' in page and "NT$255" in page
    with app.app_context():
        assert get_db().execute("SELECT quantity FROM cart_items").fetchone()[0] == 3


@pytest.mark.parametrize("quantity", ["0", "-1", "1.5", "abc", ""])
def test_invalid_quantity_is_rejected(app, client, quantity):
    login_token(client)
    response = client.post("/cart/add", data={"product_id": 1, "quantity": quantity}, follow_redirects=True)
    assert "格式不正確" in response.get_data(as_text=True)
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM cart_items").fetchone()[0] == 0


def test_update_and_remove_cart(app, client):
    login_token(client); add(client, 1, 1)
    page = client.post("/cart/update", data={"product_id": 1, "quantity": 2}, follow_redirects=True).get_data(as_text=True)
    assert 'value="2"' in page and "NT$170" in page
    page = client.post("/cart/remove", data={"product_id": 1}, follow_redirects=True).get_data(as_text=True)
    assert "購物車是空的" in page


def test_update_rejects_unavailable_product(app, client):
    login_token(client); add(client, 1, 1)
    with app.app_context(): get_db().execute("UPDATE products SET is_available=0 WHERE id=1")
    page = client.post("/cart/update", data={"product_id": 1, "quantity": 2}, follow_redirects=True).get_data(as_text=True)
    assert "已下架" in page
    with app.app_context():
        assert get_db().execute("SELECT quantity FROM cart_items").fetchone()[0] == 1


def test_empty_cart_and_checkout_states(client):
    login_token(client)
    assert "購物車是空的" in client.get("/cart").get_data(as_text=True)
    assert "目前沒有可結帳的商品" in client.get("/checkout").get_data(as_text=True)


def test_multi_merchant_order_snapshot_total_and_idempotency(app, client):
    login_token(client); add(client, 1, 2); add(client, 3, 1)
    key = checkout_key(client)
    response = client.post("/orders/create", data={"idempotency_key": key}, follow_redirects=True)
    body = response.get_data(as_text=True)
    assert "訂單已建立" in body and "NT$170" in body and "NT$25" in body
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2
        assert db.execute("SELECT COUNT(*) FROM cart_items").fetchone()[0] == 0
        snapshots = [tuple(row) for row in db.execute("SELECT product_name,unit_price,quantity FROM order_items ORDER BY id")]
        assert snapshots == [("雞腿便當", 85, 2), ("紅茶", 25, 1)]
    client.post("/orders/create", data={"idempotency_key": key})
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 2


def test_checkout_rolls_back_when_product_unavailable(app, client):
    login_token(client); add(client, 1, 1); add(client, 3, 1)
    key = checkout_key(client)
    with app.app_context(): get_db().execute("UPDATE products SET is_available=0 WHERE id=3")
    response = client.post("/orders/create", data={"idempotency_key": key}, follow_redirects=True)
    assert "已下架" in response.get_data(as_text=True)
    with app.app_context():
        db = get_db()
        assert db.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM cart_items").fetchone()[0] == 2


def test_payment_is_owner_only_and_not_repeatable(app, client):
    login_token(client); add(client, 1); key = checkout_key(client)
    client.post("/orders/create", data={"idempotency_key": key})
    with app.app_context(): order_id = get_db().execute("SELECT id FROM orders").fetchone()[0]
    other = app.test_client(); login_token(other, "student-b")
    assert "找不到可付款" in other.post("/payment/mock", data={"order_id": order_id}, follow_redirects=True).get_data(as_text=True)
    assert "模擬付款成功" in client.post("/payment/mock", data={"order_id": order_id}, follow_redirects=True).get_data(as_text=True)
    assert "已付款" in client.post("/payment/mock", data={"order_id": order_id}, follow_redirects=True).get_data(as_text=True)


def test_merchant_data_is_isolated(app, client):
    login_token(client, merchant_id=1)
    products_a = client.get("/merchant/products").get_data(as_text=True)
    assert "雞腿便當" in products_a and "紅茶" not in products_a
    with client.session_transaction() as session: session["merchant_id"] = 2
    products_b = client.get("/merchant/products").get_data(as_text=True)
    assert "紅茶" in products_b and "雞腿便當" not in products_b


def test_merchant_orders_renders_all_merchants(app, client):
    login_token(client, merchant_id=1)
    add(client, 1, 2)
    add(client, 3, 1)
    key = checkout_key(client)
    client.post("/orders/create", data={"idempotency_key": key})

    response = client.get("/merchant/orders")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "雞腿便當 × 2" in page
    assert "NT$170" in page
    assert "紅茶 × 1" in page
    assert "NT$25" in page
    assert "校園食堂" in page
    assert "飲料店" in page
    assert "未付款" in page
    assert "查看所有商家的學生訂單" in page


def test_legacy_database_migration_preserves_products(tmp_path):
    path = tmp_path / "legacy.db"
    db = sqlite3.connect(path)
    db.executescript("CREATE TABLE products(id INTEGER PRIMARY KEY,name TEXT NOT NULL,price INTEGER NOT NULL); INSERT INTO products VALUES(1,'舊商品',50);")
    db.close()
    application = create_app({"TESTING": True, "DATABASE": str(path)})
    with application.app_context():
        assert models_migrate() is True
        row = get_db().execute("SELECT p.name,p.price,m.name FROM products p JOIN merchants m ON m.id=p.merchant_id").fetchone()
        assert tuple(row) == ("舊商品", 50, "校園食堂")


def models_migrate():
    from backend.models import migrate_legacy_db
    return migrate_legacy_db()
