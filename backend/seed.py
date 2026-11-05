from backend.app import create_app
from backend.models import get_db, init_db

DEFAULT_PRODUCTS = (("雞腿便當", 85), ("紅茶", 25))

def seed_products():
    db = get_db()
    for name, price in DEFAULT_PRODUCTS:
        if not db.execute("SELECT 1 FROM products WHERE name = ? AND price = ?", (name, price)).fetchone():
            db.execute("INSERT INTO products (name, price) VALUES (?, ?)", (name, price))
    db.commit()

def main():
    app = create_app()
    with app.app_context():
        init_db(); seed_products()
    print("Seeded default products without deleting or duplicating existing data.")

if __name__ == "__main__": main()
