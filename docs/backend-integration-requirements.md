# 後端整合需求：改用 FrontUI 伺服器端渲染契約

> 對象：後端負責人（C）
> 目的：讓 `Backend` 分支的 Flask 應用支援 FrontUI 已完成的 Jinja2 頁面與表單 POST 流程。
> 依據：`ui.md`、`docs/ui-backend-contract.md`、FrontUI 分支的 `templates/` 與 `static/`。
> 結論：**不以 JSON API 作為 UI 資料來源**，改為「頁面路由 + `render_template` 傳入資料 + HTML 表單 POST」。

---

## 0. 摘要（TL;DR）

目前 `Backend` 是「JSON API + 空模板」；FrontUI 是「Jinja 變數 + 表單 POST」。要採用 FrontUI 方式，後端必須：

1. 把頁面路由改成 `render_template(..., **context)`，直接傳入商品、購物車、訂單資料。
2. 新增資料表：`merchants`、`carts`、`cart_items`、`checkout_batches`。
3. 擴充 `products`、`orders`、`order_items` 欄位。
4. 實作 11 個頁面／表單路由（見第 6 節）。
5. 加入 session 身分（學生 `cart_token`、商家 `merchant_id`）。
6. 實作多商家購物車、交易式結帳、`idempotency_key` 防重複、模擬付款。
7. 更新 seed、測試、`integration/api-contract.md` 與 README。

> 重要：目前 `/api/orders`、`/api/orders/<id>/simulate-payment` 都是 501 占位，且沒有購物車 API。若採用 FrontUI 契約，**不要**再另外維護一套 JSON API 商業邏輯，避免兩套行為不一致。

---

## 1. 與目前 Backend 的差異總表

| 項目 | 目前 Backend | 需要改成（FrontUI 契約） |
| --- | --- | --- |
| 頁面資料來源 | 頁面路由 `render_template(template)` 不帶資料 | `render_template` 傳入 `products`、`merchant_groups`、`total`、`orders` 等 |
| 前端取得資料 | 規劃用 JS `fetch` JSON API | Jinja 直接輸出；表單 POST 後 redirect + Flash |
| 商品 API | `GET/POST /api/products` | 保留與否皆可，但 UI 不使用；以 `GET /menu`、`POST /merchant/products` 為主 |
| 訂單 API | `/api/orders` 回 501 | 改為 `POST /orders/create`、`POST /payment/mock` |
| 購物車 | 無資料表、無 API | `carts`、`cart_items` 資料表 + `/cart/*` 路由 |
| 商家 | 無 `merchants` 表，單商家 | `merchants` 表 + `products.merchant_id` + session 商家 |
| 商品欄位 | `id`、`name`、`price` | 加 `merchant_id`、`description`、`image_url`、`is_available` |
| 訂單欄位 | `id`、`total_amount`、`payment_status`、`created_at` | 加 `merchant_id`、`checkout_batch_id`、`session_token` |
| 訂單明細 | `product_id`、`quantity`、`unit_price` | 加 `product_name` 快照；`subtotal` 由後端計算 |
| 重複結帳 | 無 | `checkout_batches` + `(session_token, idempotency_key)` 唯一鍵 |
| 身分 | 無 session 身分 | `session["cart_token"]`、`session["merchant_id"]`、`SECRET_KEY` |
| 模板位置 | `frontend/templates/student/*`、`frontend/templates/merchant/*` | 對齊 FrontUI 的 `templates/`（見第 3 節） |
| 測試 | 預期 `/api/orders` 回 501、頁面空渲染 | 改測購物車、結帳、付款、權限、交易回滾 |
| 契約文件 | `integration/api-contract.md`（JSON API） | 改指向 `docs/ui-backend-contract.md`，避免兩份衝突 |

---

## 2. 架構決策

1. **單一 Flask 應用**：保留 `backend/app.py` 的 `create_app()` 架構即可，但頁面路由要傳資料。
2. **資料傳遞**：使用伺服器端渲染，不用前端 `fetch` 取頁面資料。
3. **表單 POST**：購物車與結帳一律用 HTML 表單 POST，成功後 redirect + Flash。
4. **金額信任邊界**：前端只送 `product_id`、`quantity`、`idempotency_key`、`order_id`；價格、總額、商家一律由後端依資料庫計算。
5. **付款**：僅模擬付款，建立訂單一律 `unpaid`，付款成功才更新為 `paid`。
6. **不新增 ORM**：沿用 Python 標準庫 `sqlite3`。

---

## 3. 目錄與 Flask 設定

### 建議方案（沿用 FrontUI 現有檔案）

FrontUI 的模板在 repo 根目錄 `templates/`、靜態檔在 `static/`。建議後端把 Flask 指向這兩個資料夾，避免搬動已完成的前端：

```python
from pathlib import Path
from flask import Flask

BASE_DIR = Path(__file__).resolve().parent.parent

def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret")
    # ... 其餘設定
```

要渲染的模板名稱（不可改名）：

- `menu.html`
- `cart.html`
- `checkout.html`
- `merchant.html`
- `orders.html`
- `base.html`
- `partials/navbar.html`
- `partials/order_summary.html`

### 需移除或停用的重複模板

目前 `frontend/templates/student/*`、`frontend/templates/merchant/*` 是空骨架。整合後請**擇一保留**：

- 建議：以 FrontUI 的 `templates/` 為準，刪除或停用 `frontend/templates/` 的重複骨架。
- 若團隊決定統一放 `frontend/templates/`，則必須把 FrontUI 模板搬過去，並同步修改所有 `render_template()` 名稱；不要兩套並存。

### JSON API 的處置

- `GET/POST /api/products` 可保留作除錯或未來商家 JS 使用，但**不得成為學生頁面的資料來源**。
- `/api/orders`、`/api/orders/<id>/simulate-payment` 請改為頁面／表單路由，或明確標示為 deprecated。
- 若保留 API，請確保它與表單路由共用同一套 service 邏輯，避免金額計算不一致。

---

## 4. 資料庫 Schema 變更

目前 `backend/schema.sql` 只有 `products`、`orders`、`order_items`，且欄位不足。請調整如下。

### 4.1 新增 `merchants`

```sql
CREATE TABLE IF NOT EXISTS merchants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE CHECK (length(trim(name)) > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 擴充 `products`

```sql
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_id INTEGER NOT NULL,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT,
    price INTEGER NOT NULL CHECK (typeof(price) = 'integer' AND price > 0),
    image_url TEXT,
    is_available INTEGER NOT NULL DEFAULT 1 CHECK (is_available IN (0, 1)),
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE RESTRICT
);
```

- `description` 為 `ui.md` 要求的商品描述；可為 NULL，前端會顯示「尚無商品描述」。
- `image_url` 可為 NULL，前端會顯示佔位區塊。
- `is_available = 0` 時前端顯示「已下架」且不可加入購物車。

### 4.3 新增 `carts`

```sql
CREATE TABLE IF NOT EXISTS carts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 4.4 新增 `cart_items`

```sql
CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cart_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (typeof(quantity) = 'integer' AND quantity > 0),
    UNIQUE (cart_id, product_id),
    FOREIGN KEY (cart_id) REFERENCES carts(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
```

### 4.5 新增 `checkout_batches`

```sql
CREATE TABLE IF NOT EXISTS checkout_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (session_token, idempotency_key)
);
```

### 4.6 擴充 `orders`

```sql
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL,
    merchant_id INTEGER NOT NULL,
    checkout_batch_id INTEGER,
    total_amount INTEGER NOT NULL CHECK (typeof(total_amount) = 'integer' AND total_amount > 0),
    payment_status TEXT NOT NULL DEFAULT 'unpaid'
        CHECK (payment_status IN ('unpaid', 'paid', 'failed')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE RESTRICT,
    FOREIGN KEY (checkout_batch_id) REFERENCES checkout_batches(id) ON DELETE SET NULL
);
```

- 契約中的 `total` 對應資料庫 `total_amount`，在組 context 時改名為 `total`。
- `payment_status` 目前有 `failed`。前端只會顯示「已付款／未付款」，若保留 `failed` 請告知前端補樣式；若不需要可移除，只留 `unpaid`、`paid`。

### 4.7 擴充 `order_items`

```sql
CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (typeof(quantity) = 'integer' AND quantity > 0),
    unit_price INTEGER NOT NULL CHECK (typeof(unit_price) = 'integer' AND unit_price > 0),
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
);
```

- `product_name`、`unit_price` 是建立訂單當下的快照。
- `subtotal = unit_price * quantity` 由後端組 context 時計算，不需額外欄位。

### 4.8 Migration 注意事項

`schema.sql` 使用 `CREATE TABLE IF NOT EXISTS`，**既有資料庫不會自動新增欄位**。請擇一處理：

- Demo 環境：刪除 `instance/campus_ordering.db`，重新 `flask --app backend.app init-db` 與 seed。
- 需要保留資料：新增 migration 腳本（`ALTER TABLE ... ADD COLUMN`），不可只改 `schema.sql`。

---

## 5. Session 身分（Demo）

1. `app.config["SECRET_KEY"]` 必須設定，否則 Flash 與 session 無法運作。
2. 學生身分：第一次請求時若無 `session["cart_token"]`，產生 UUID 並存入 session；`carts.session_token`、`orders.session_token`、`checkout_batches.session_token` 都用此值。
3. 商家身分：`session["merchant_id"]` 代表目前商家。
   - 若尚未設定，Demo 可自動選擇第一位商家並寫入 session。
   - 若要做切換，請新增 `POST /merchant/select`（表單欄位 `merchant_id`），只更新 session，不接受查詢字串指定。
4. 所有查詢與付款都必須用 session 身分過濾，**不可**信任表單或 query string 傳入的 `merchant_id`／`session_token`。

---

## 6. 路由與模板契約

### 6.1 路由總表

| 功能 | Method | 路徑 | 表單／輸入 | Context / 行為 |
| --- | --- | --- | --- | --- |
| 學生菜單 | GET | `/menu` | 無 | `products` |
| 購物車 | GET | `/cart` | 無 | `merchant_groups`、`total` |
| 加入購物車 | POST | `/cart/add` | `product_id`、`quantity` | 成功 redirect `/cart` + Flash；失敗 redirect `/menu` + Flash |
| 更新購物車 | POST | `/cart/update` | `product_id`、`quantity` | redirect `/cart` |
| 移除項目 | POST | `/cart/remove` | `product_id` | redirect `/cart` |
| 結帳頁 | GET | `/checkout` | 無 | `merchant_groups`、`total`、`idempotency_key`、選用 `orders` |
| 建立訂單 | POST | `/orders/create` | `idempotency_key` | 建立多張訂單後 redirect `/checkout` + Flash |
| 模擬付款 | POST | `/payment/mock` | `order_id` | 更新單張訂單後 redirect `/checkout` + Flash |
| 商家商品管理 | GET | `/merchant/products` | 無（商家由 session 決定） | `products` |
| 新增商品 | POST | `/merchant/products` | `name`、`price` | redirect `/merchant/products` + Flash |
| 商家訂單 | GET | `/merchant/orders` | 無（商家由 session 決定） | `orders` |

### 6.2 `url_for()` endpoint 名稱（必須一致）

FrontUI 模板已寫死下列 endpoint 名稱；後端路由函式名稱或 `add_url_rule` 的 endpoint 必須相同，否則 `url_for()` 會報錯：

| endpoint 名稱 | 路徑 |
| --- | --- |
| `menu` | `GET /menu` |
| `cart` | `GET /cart` |
| `add_to_cart` | `POST /cart/add` |
| `update_cart` | `POST /cart/update` |
| `remove_cart_item` | `POST /cart/remove` |
| `checkout` | `GET /checkout` |
| `create_order` | `POST /orders/create` |
| `mock_payment` | `POST /payment/mock` |
| `merchant_products` | `GET /merchant/products` |
| `merchant_create_product` | `POST /merchant/products` |
| `merchant_orders` | `GET /merchant/orders` |

靜態檔則使用 `url_for('static', filename='css/style.css')` 與 `url_for('static', filename='js/cart.js')`。

### 6.3 模板變數格式

> 請傳入 **plain dict / list**（不要自訂 class）。FrontUI 的 `order_summary.html` 使用 `group['items']` 取值，`sqlite3.Row` 或 dict 可用，自訂物件會失敗。

#### `menu.html`

```python
products = [
    {
        "id": 1,
        "merchant_id": 1,
        "merchant_name": "校園食堂",
        "name": "雞腿便當",
        "description": "招牌雞腿搭配三樣配菜",
        "price": 85,
        "image_url": None,
        "is_available": True,
    },
]
```

- 建議傳入所有商品（含未上架），前端會顯示「已下架」；若只傳上架商品，前端不會顯示下架狀態。

#### `cart.html` / `checkout.html`

```python
merchant_groups = [
    {
        "merchant_id": 1,
        "merchant_name": "校園食堂",
        "items": [
            {
                "merchant_id": 1,
                "product_id": 1,
                "name": "雞腿便當",
                "unit_price": 85,
                "quantity": 2,
                "subtotal": 170,
            },
        ],
        "subtotal": 170,
    },
]
total = 170
idempotency_key = "uuid-string"  # 只有 checkout.html 需要
```

#### `checkout.html` 的 `orders`

建立訂單後 redirect 回 `/checkout` 時，若購物車已清空，請傳入最近一次結帳批次的訂單，讓前端顯示付款狀態：

```python
orders = [
    {
        "order_id": 101,
        "merchant_id": 1,
        "merchant_name": "校園食堂",
        "created_at": "2026-11-09 12:00:00",
        "items": [
            {
                "product_id": 1,
                "name": "雞腿便當",
                "unit_price": 85,
                "quantity": 2,
                "subtotal": 170,
            },
        ],
        "total": 170,
        "payment_status": "unpaid",
    },
]
```

#### `merchant.html`

```python
products = [
    {"id": 1, "name": "雞腿便當", "price": 85, "is_available": True},
]
```

#### `orders.html`

```python
orders = [
    {
        "order_id": 101,
        "merchant_id": 1,
        "merchant_name": "校園食堂",
        "created_at": "2026-11-09 12:00:00",
        "items": [
            {"product_id": 1, "name": "雞腿便當", "unit_price": 85, "quantity": 2, "subtotal": 170},
        ],
        "total": 170,
        "payment_status": "paid",
    },
]
```

---

## 7. 業務邏輯與驗證

### 7.1 購物車

- `POST /cart/add`
  - `product_id` 必須存在且 `is_available = 1`。
  - `quantity` 必須為整數且 `>= 1`。
  - 同商品重複加入時，建議累加數量（`ON CONFLICT` 或先查再更新）。
  - 成功：Flash `success`「已加入購物車」，redirect `/cart`。
  - 失敗：Flash `danger`／`warning`，redirect `/menu`。
- `POST /cart/update`
  - `quantity < 1` 時不可更新，Flash `warning`，提示改用移除。
  - 只更新目前 session 購物車內的項目。
- `POST /cart/remove`
  - 只刪除目前 session 購物車內的項目；不存在時 Flash `info`。
- 所有 `merchant_id` 一律由 `products` 查詢，不可接受前端傳入。

### 7.2 建立訂單（`POST /orders/create`）

必須在同一個 SQLite Transaction 內完成，建議 `BEGIN IMMEDIATE`：

1. 依 `session["cart_token"]` 取得 `cart_items`。
2. JOIN `products`、`merchants` 取得 `merchant_id`、`name`、`price`、`is_available`。
3. 驗證購物車非空、所有商品存在且 `is_available = 1`。
4. 依 `products.merchant_id` 分組。
5. 用資料庫價格重算每個商家小計與訂單總額。
6. 檢查 `checkout_batches` 是否已有 `(session_token, idempotency_key)`：
   - 若存在：直接載入該批次訂單，Flash `info`「訂單已建立」，redirect `/checkout`，**不建立新訂單**。
7. 新增 `checkout_batches`。
8. 每個商家新增一張 `orders`（`payment_status = 'unpaid'`）與 `order_items` 快照（`product_name`、`unit_price`、`quantity`）。
9. 清空該購物車的 `cart_items`。
10. Commit。
11. 任一驗證或寫入失敗：Rollback，購物車保持不變，Flash `danger`，redirect `/checkout`。

### 7.3 模擬付款（`POST /payment/mock`）

- `order_id` 必須存在、屬於目前 `session["cart_token"]`、且 `payment_status = 'unpaid'`。
- 模擬成功後更新為 `paid` 並 commit。
- 已付款：Flash `info`／`warning`，不可重複付款。
- 非本人訂單或不存在：Flash `danger`，不可洩漏其他訂單資訊。
- 失敗情境（若模擬失敗）：保持 `unpaid` 或設 `failed`，但不得誤設 `paid`。

### 7.4 商家

- `GET /merchant/products`：只查目前 session 商家的商品（含未上架）。
- `POST /merchant/products`：`name` 不可空白、`price` 必須為正整數；`merchant_id` 取自 session。
- `GET /merchant/orders`：只查目前 session 商家的訂單。
- 不可用 query string 或表單任意指定要查詢的商家。

### 7.5 錯誤訊息

- 一律使用使用者可理解的中文 Flash 訊息。
- 不可把 traceback、SQL 或內部錯誤直接輸出到頁面。
- Flash 類別沿用 Bootstrap：`success`、`danger`、`warning`、`info`。

---

## 8. Flash 與 CSRF

- `base.html` 已會顯示 Flash；後端只要 `flash(message, category)` 即可。
- 目前 FrontUI 表單**沒有 CSRF token**：
  - 若後端啟用 Flask-WTF `CSRFProtect`，所有 POST 會失敗。
  - 請先決定：Demo 階段不啟用 CSRF，或通知前端在每個表單加入 `{{ csrf_token() }}` hidden 欄位。
- 不要在未協調的情況下單方面開啟 CSRF。

---

## 9. Seed 資料

請更新 `backend/seed.py`：

- 建立至少 2 位商家（例如「校園食堂」、「飲料店」），方便驗證多商家購物車。
- 每個商家建立 1～2 個商品，包含 `description`、`price`、`is_available`。
- Seed 必須可重複執行且不重複插入（沿用目前 idempotent 設計）。
- 範例驗收：85 元商品 × 2 + 25 元商品 × 1 = 195 元，總額由後端計算。

---

## 10. 測試需求

目前 `integration/tests/test_smoke.py` 預期 `/api/orders` 回 501、頁面只檢查 200。請調整並新增：

### 必測案例

- [ ] `GET /menu` 輸出 seed 商品名稱與價格。
- [ ] `POST /cart/add` 後 `cart_items` 有資料，`GET /cart` 顯示數量與小計。
- [ ] 同商品重複加入時數量累加。
- [ ] `quantity < 1` 被拒絕，購物車不變。
- [ ] `POST /cart/update` 更新數量，總額正確。
- [ ] `POST /cart/remove` 移除項目。
- [ ] 空購物車的 `/cart`、`/checkout` 顯示空狀態。
- [ ] `POST /orders/create` 依商家建立多張訂單，購物車清空。
- [ ] 訂單明細的 `product_name`、`unit_price` 是建立當下快照。
- [ ] 同一 `(session_token, idempotency_key)` 重送不會重複建立訂單。
- [ ] 商品已下架時結帳失敗，Rollback 後購物車不變、沒有部分訂單。
- [ ] `POST /payment/mock` 只能付款自己的訂單，不能重複付款。
- [ ] 商家 A 看不到商家 B 的商品與訂單。
- [ ] Flash 類別與訊息正確（成功／失敗／空資料）。

### 測試方式

- 使用 `create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})`。
- 使用 `client.post(..., follow_redirects=True)` 驗證頁面結果。
- 保留 `GET /health`、schema／外鍵、seed idempotent 測試。

---

## 11. 文件與契約同步

- `integration/api-contract.md` 目前描述 JSON API，與 FrontUI 契約衝突。請改為：
  - 標註「本專案 UI 採用伺服器端渲染 + 表單 POST」。
  - 連到 `docs/ui-backend-contract.md` 作為正式契約。
  - 若保留 `/api/*`，清楚標示用途與非 UI 資料來源。
- 更新 `README.md`：
  - 啟動方式（`run.py`、`init-db`、seed）。
  - 頁面路由與表單欄位。
  - Demo 身分切換方式。
- 不要同時維護兩份互相矛盾的契約。

---

## 12. 建議實作順序

1. 調整 `create_app()` 的 `template_folder`／`static_folder`、`SECRET_KEY`。
2. 更新 `backend/schema.sql` 與 migration 策略。
3. 更新 `backend/seed.py`（商家＋商品）。
4. 在 `backend/models.py` 新增／調整資料存取函式：
   - `get_or_create_cart(session_token)`
   - `list_products()`
   - `list_products_by_merchant(merchant_id)`
   - `add_cart_item` / `update_cart_item` / `remove_cart_item`
   - `get_cart_groups(session_token)`
   - `create_orders_from_cart(session_token, idempotency_key)`
   - `get_orders_by_batch(session_token, batch_id)` / `get_recent_orders(session_token)`
   - `pay_order(session_token, order_id)`
   - `list_orders_by_merchant(merchant_id)`
5. 改寫 `backend/app.py` 的頁面路由與表單路由。
6. 更新測試。
7. 更新契約文件與 README。
8. 與前端一起跑一次完整流程（加入購物車 → 結帳 → 付款）。

---

## 13. 驗收清單（Definition of Done）

- [ ] `python run.py` 可啟動，`/menu`、`/cart`、`/checkout`、`/merchant/products`、`/merchant/orders` 皆 200。
- [ ] 頁面資料由後端傳入，前端不需 `fetch` 即可看到商品。
- [ ] 購物車可加入、更新、移除，金額由後端計算。
- [ ] 多商家購物車可正確分組與計算小計。
- [ ] 結帳建立多張訂單、清空購物車、失敗時完整 Rollback。
- [ ] 重複送出同一 `idempotency_key` 不會重複建單。
- [ ] 模擬付款只更新自己的未付款訂單，且不可重複付款。
- [ ] 商家只能看到自己的商品與訂單。
- [ ] Flash 成功／失敗／空資料狀態正常。
- [ ] 所有測試通過，且沒有 501 占位路由被 UI 使用。
- [ ] `docs/ui-backend-contract.md` 與 `integration/api-contract.md` 不再互相矛盾。

---

## 14. 不要做的事

- 不要信任前端傳來的價格、總額、付款狀態或 `merchant_id`。
- 不要讓前端直接指定 `session_token` 或查詢他人訂單。
- 不要建立真正的金流或收集信用卡資料。
- 不要只改 `schema.sql` 卻不處理既有資料庫 migration。
- 不要同時保留「JSON API 商業邏輯」與「表單路由商業邏輯」兩套實作。
- 不要把例外堆疊或 SQL 錯誤直接顯示給使用者。
- 不要在未通知前端的情況下啟用 CSRF。
