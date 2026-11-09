from backend.app import create_app
from backend.models import get_db, init_db

DEFAULT_DATA = (
    ("校園食堂", (("雞腿便當", "招牌雞腿搭配三樣配菜", 85, 1), ("排骨便當", "酥炸排骨便當", 90, 1))),
    ("飲料店", (("紅茶", "清爽紅茶", 25, 1), ("奶茶", "香濃奶茶", 35, 1))),
)


def seed_data():
    db = get_db()
    for merchant_name, products in DEFAULT_DATA:
        db.execute("INSERT OR IGNORE INTO merchants(name) VALUES (?)", (merchant_name,))
        merchant_id = db.execute("SELECT id FROM merchants WHERE name=?", (merchant_name,)).fetchone()["id"]
        for name, description, price, available in products:
            exists = db.execute(
                "SELECT 1 FROM products WHERE merchant_id=? AND name=?", (merchant_id, name)
            ).fetchone()
            if not exists:
                db.execute(
                    "INSERT INTO products(merchant_id,name,description,price,is_available) VALUES (?,?,?,?,?)",
                    (merchant_id, name, description, price, available),
                )


def main():
    application = create_app()
    with application.app_context():
        init_db()
        seed_data()
    print("已建立示範商家與商品；重複執行不會重複新增。")


if __name__ == "__main__":
    main()
