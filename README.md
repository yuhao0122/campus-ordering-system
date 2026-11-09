# COS 校園點餐系統

以 Flask、Jinja2 與 SQLite 實作的校園點餐 Demo。UI 採伺服器端渲染及 HTML 表單 POST；價格、商家、總額與付款狀態都由後端判定，不信任瀏覽器輸入。本專案只有模擬付款，不得用於真實金流或公開部署。

## Windows PowerShell 啟動

在 Repository 根目錄執行：

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m flask --app app init-db
.\.venv\Scripts\python.exe -m backend.seed
.\.venv\Scripts\python.exe run.py
```

若舊版 `instance/campus_ordering.db` 已存在，`init-db` 會停止並提示 migration；保留資料的升級指令是：

```powershell
.\.venv\Scripts\python.exe -m flask --app app migrate-db
.\.venv\Scripts\python.exe -m backend.seed
```

不要直接刪除有需要保留資料的 DB。測試：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 頁面與表單

| Method | 路徑 | 用途／欄位 |
|---|---|---|
| GET | `/menu` | 商品菜單 |
| GET | `/cart` | 多商家購物車 |
| POST | `/cart/add` | `product_id`, `quantity` |
| POST | `/cart/update` | `product_id`, `quantity` |
| POST | `/cart/remove` | `product_id` |
| GET | `/checkout` | 結帳摘要與最近訂單 |
| POST | `/orders/create` | `idempotency_key` |
| POST | `/payment/mock` | `order_id` |
| GET/POST | `/merchant/products` | 商品列表；新增欄位 `name`, `price` |
| GET | `/merchant/orders` | 所有商家的訂單總覽 |
| POST | `/merchant/select` | Demo 商家切換欄位 `merchant_id` |

學生以 session `cart_token` 隔離購物車／訂單；商家商品管理以 session `merchant_id` 限定目前商家，商家訂單頁則提供所有商家的訂單總覽並逐筆標示商家。seed 建立「校園食堂」與「飲料店」，預設使用第一位商家。切換路由已提供，前端切換控制可後續討論。

正式 UI 契約見 `docs/ui-backend-contract.md`；後端整合摘要見 `integration/api-contract.md`。
