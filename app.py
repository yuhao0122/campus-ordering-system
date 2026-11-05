import os

from flask import Flask, flash, redirect, render_template, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-ui-skeleton")


@app.get("/")
def index():
    return redirect(url_for("menu"))


@app.get("/menu")
def menu():
    return render_template("menu.html", products=[])


@app.get("/cart")
def cart():
    return render_template("cart.html", cart_items=[], total=0)


@app.post("/cart/add")
def add_to_cart():
    flash("加入購物車功能尚未串接後端。", "warning")
    return redirect(url_for("menu"))


@app.post("/cart/update")
def update_cart():
    flash("更新購物車功能尚未串接後端。", "warning")
    return redirect(url_for("cart"))


@app.post("/cart/remove")
def remove_cart_item():
    flash("移除商品功能尚未串接後端。", "warning")
    return redirect(url_for("cart"))


@app.get("/checkout")
def checkout():
    return render_template("checkout.html", cart_items=[], total=0)


@app.post("/orders/create")
def create_order():
    flash("建立訂單功能尚未串接後端。", "warning")
    return redirect(url_for("checkout"))


@app.post("/payment/mock")
def mock_payment():
    flash("模擬付款功能尚未串接後端。", "warning")
    return redirect(url_for("checkout"))


@app.get("/merchant/products")
def merchant_products():
    return render_template("merchant.html", products=[])


@app.post("/merchant/products")
def merchant_create_product():
    flash("新增商品功能尚未串接後端。", "warning")
    return redirect(url_for("merchant_products"))


@app.get("/merchant/orders")
def merchant_orders():
    return render_template("orders.html", orders=[])


if __name__ == "__main__":
    app.run(debug=True)
