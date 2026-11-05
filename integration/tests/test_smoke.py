import sqlite3
import pytest
from backend.app import create_app
from backend.models import get_db, init_db
from backend.seed import seed_products

@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context(): init_db()
    return app

@pytest.fixture
def client(app): return app.test_client()

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200 and response.get_json() == {"status": "ok"}

def test_init_is_idempotent_and_tables_exist(app):
    with app.app_context():
        db = get_db(); db.execute("INSERT INTO products(name, price) VALUES (?, ?)", ("保留", 1)); db.commit(); init_db()
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"products", "orders", "order_items"} <= tables
        assert db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 1

def test_products_empty_then_persist(client, app):
    assert client.get("/api/products").get_json() == []
    response = client.post("/api/products", json={"name": " 紅茶 ", "price": 25})
    assert response.status_code == 201 and response.get_json()["name"] == "紅茶"
    with app.app_context(): assert get_db().execute("SELECT price FROM products").fetchone()[0] == 25
    assert client.get("/api/products").get_json()[0]["price"] == 25

@pytest.mark.parametrize("payload", [{"name":" ","price":1},{"name":"x","price":0},{"name":"x","price":-1},{"name":"x","price":1.5},{"name":"x","price":"1"},{"name":"x","price":True}])
def test_invalid_products_do_not_insert(client, app, payload):
    response = client.post("/api/products", json=payload)
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "invalid_input"
    with app.app_context(): assert get_db().execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0

def test_foreign_keys_enabled(app):
    with app.app_context():
        db = get_db(); assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError): db.execute("INSERT INTO order_items(order_id, product_id, quantity, unit_price) VALUES (999,999,1,1)")

def test_seed_is_idempotent(app):
    with app.app_context():
        seed_products(); seed_products()
        assert get_db().execute("SELECT COUNT(*) FROM products").fetchone()[0] == 2

@pytest.mark.parametrize("path", ["/menu","/cart","/checkout","/merchant/products","/merchant/orders"])
def test_pages_render(client, path): assert client.get(path).status_code == 200

@pytest.mark.parametrize("method,path", [("post","/api/orders"),("get","/api/orders"),("post","/api/orders/1/simulate-payment")])
def test_planned_apis_are_not_fake_success(client, method, path):
    response = getattr(client, method)(path, json={})
    assert response.status_code == 501 and response.get_json()["error"]["code"] == "not_implemented"
