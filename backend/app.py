import click
from flask import Flask, jsonify, redirect, render_template, request, url_for
from backend import models

def invalid_input(message):
    return jsonify(error={"code": "invalid_input", "message": message}), 400

def create_app(test_config=None):
    app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
    app.config.from_mapping(DATABASE=str(models.DEFAULT_DATABASE))
    if test_config: app.config.update(test_config)
    app.teardown_appcontext(models.close_db)

    @app.cli.command("init-db")
    def init_db_command():
        models.init_db()
        click.echo("Initialized the database without deleting existing data.")

    @app.get("/")
    def index(): return redirect(url_for("menu"))

    @app.get("/health")
    def health(): return jsonify(status="ok")

    @app.route("/api/products", methods=["GET", "POST"])
    def products():
        if request.method == "GET":
            return jsonify([dict(row) for row in models.list_products()])
        if not request.is_json: return invalid_input("Content-Type must be application/json.")
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict): return invalid_input("Request body must be a JSON object.")
        name, price = payload.get("name"), payload.get("price")
        if not isinstance(name, str) or not name.strip(): return invalid_input("name must be a non-empty string.")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0: return invalid_input("price must be a positive integer.")
        return jsonify(models.create_product(name.strip(), price)), 201

    def not_implemented(**kwargs):
        return jsonify(error={"code": "not_implemented", "message": "This API is planned but not implemented."}), 501
    app.add_url_rule("/api/orders", "orders", not_implemented, methods=["GET", "POST"])
    app.add_url_rule("/api/orders/<int:order_id>/simulate-payment", "simulate_payment", not_implemented, methods=["POST"])

    pages = {"/menu": ("menu", "student/menu.html"), "/cart": ("cart", "student/cart.html"), "/checkout": ("checkout", "student/checkout.html"), "/merchant/products": ("merchant_products", "merchant/products.html"), "/merchant/orders": ("merchant_orders", "merchant/orders.html")}
    for rule, (endpoint, template) in pages.items():
        app.add_url_rule(rule, endpoint, lambda template=template: render_template(template))
    return app

app = create_app()
