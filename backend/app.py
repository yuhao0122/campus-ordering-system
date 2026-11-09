import os
from uuid import uuid4

import click
from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from backend import models


def _positive_int(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if str(value).strip() == str(number) and number > 0 else None


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=str(models.REPO_ROOT / "templates"),
        static_folder=str(models.REPO_ROOT / "static"),
    )
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-secret-change-before-deployment"),
        DATABASE=str(models.DEFAULT_DATABASE),
    )
    if test_config:
        app.config.update(test_config)
    app.teardown_appcontext(models.close_db)

    @app.before_request
    def ensure_demo_identity():
        session.setdefault("cart_token", str(uuid4()))
        if "merchant_id" not in session:
            merchants = models.list_merchants() if _database_ready() else []
            if merchants:
                session["merchant_id"] = merchants[0]["id"]

    def _database_ready():
        return models._table_exists(models.get_db(), "merchants")

    @app.cli.command("init-db")
    def init_db_command():
        models.init_db()
        click.echo("資料庫已初始化；既有資料未被刪除。")

    @app.cli.command("migrate-db")
    def migrate_db_command():
        changed = models.migrate_legacy_db()
        click.echo("舊版資料庫已保留資料並升級。" if changed else "資料庫已是最新版。")

    @app.get("/")
    def index():
        return redirect(url_for("menu"))

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/menu")
    def menu():
        return render_template("menu.html", products=models.list_products())

    @app.get("/cart")
    def cart():
        groups, total = models.get_cart_groups(session["cart_token"])
        return render_template("cart.html", merchant_groups=groups, total=total)

    @app.post("/cart/add")
    def add_to_cart():
        product_id = _positive_int(request.form.get("product_id"))
        quantity = _positive_int(request.form.get("quantity"))
        if product_id is None or quantity is None:
            flash("商品或數量格式不正確。", "warning")
            return redirect(url_for("menu"))
        try:
            models.add_cart_item(session["cart_token"], product_id, quantity)
            session.pop("checkout_key", None)
        except models.DomainError as error:
            flash(str(error), "danger")
            return redirect(url_for("menu"))
        flash("已加入購物車。", "success")
        return redirect(url_for("menu"))

    @app.post("/cart/update")
    def update_cart():
        product_id = _positive_int(request.form.get("product_id"))
        quantity = _positive_int(request.form.get("quantity"))
        if product_id is None or quantity is None:
            flash("數量必須是大於 0 的整數；若不要此商品請使用移除。", "warning")
            return redirect(url_for("cart"))
        try:
            models.update_cart_item(session["cart_token"], product_id, quantity)
            flash("購物車數量已更新。", "success")
        except models.DomainError as error:
            flash(str(error), "warning")
        return redirect(url_for("cart"))

    @app.post("/cart/remove")
    def remove_cart_item():
        product_id = _positive_int(request.form.get("product_id"))
        if product_id and models.remove_cart_item(session["cart_token"], product_id):
            flash("商品已從購物車移除。", "success")
        else:
            flash("購物車中沒有這項商品。", "info")
        return redirect(url_for("cart"))

    @app.get("/checkout")
    def checkout():
        groups, total = models.get_cart_groups(session["cart_token"])
        key = session.get("checkout_key")
        if groups and not key:
            key = session["checkout_key"] = str(uuid4())
        return render_template(
            "checkout.html",
            merchant_groups=groups,
            total=total,
            idempotency_key=key,
            orders=models.get_recent_orders(session["cart_token"]),
        )

    @app.post("/orders/create")
    def create_order():
        key = request.form.get("idempotency_key", "").strip()
        if not key or key != session.get("checkout_key"):
            flash("結帳資訊已過期，請重新確認購物車。", "danger")
            return redirect(url_for("checkout"))
        try:
            _, replayed = models.create_orders_from_cart(session["cart_token"], key)
            flash("訂單已建立。" if not replayed else "訂單已建立，未重複送出。", "info" if replayed else "success")
        except models.DomainError as error:
            flash(str(error), "danger")
        except Exception:
            current_app.logger.exception("建立訂單失敗")
            flash("建立訂單失敗，購物車內容已保留。", "danger")
        return redirect(url_for("checkout"))

    @app.post("/payment/mock")
    def mock_payment():
        order_id = _positive_int(request.form.get("order_id"))
        if order_id is None:
            flash("訂單資料不正確。", "danger")
            return redirect(url_for("checkout"))
        try:
            changed = models.pay_order(session["cart_token"], order_id)
            flash("模擬付款成功。" if changed else "此訂單已付款。", "success" if changed else "info")
        except models.DomainError as error:
            flash(str(error), "danger")
        return redirect(url_for("checkout"))

    def current_merchant_id():
        merchant_id = session.get("merchant_id")
        if merchant_id is None:
            raise models.DomainError("目前沒有可用商家，請先執行 seed。")
        return merchant_id

    @app.get("/merchant/products")
    def merchant_products():
        try:
            products = models.list_products_by_merchant(current_merchant_id())
        except models.DomainError as error:
            flash(str(error), "warning")
            products = []
        return render_template("merchant.html", products=products)

    @app.post("/merchant/products")
    def merchant_create_product():
        name = request.form.get("name", "").strip()
        price = _positive_int(request.form.get("price"))
        if not name or price is None:
            flash("商品名稱不可空白，價格必須是正整數。", "warning")
        else:
            try:
                models.create_product(current_merchant_id(), name, price)
                flash("商品新增成功。", "success")
            except models.DomainError as error:
                flash(str(error), "danger")
        return redirect(url_for("merchant_products"))

    @app.get("/merchant/orders")
    def merchant_orders():
        return render_template("orders.html", orders=models.list_orders())

    @app.post("/merchant/select")
    def merchant_select():
        merchant_id = _positive_int(request.form.get("merchant_id"))
        allowed = {merchant["id"] for merchant in models.list_merchants()}
        if merchant_id not in allowed:
            flash("找不到指定商家。", "danger")
        else:
            session["merchant_id"] = merchant_id
            flash("商家身分已切換。", "success")
        return redirect(url_for("merchant_products"))

    return app


app = create_app()
