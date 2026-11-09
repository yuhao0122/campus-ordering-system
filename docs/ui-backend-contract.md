# UI / 後端整合契約（多商家購物車版）

> 狀態：**設計已確認，待實作**。
> 目前程式仍是 UI 骨架；本文件與 `docs/api-request.schema.json`、`docs/api-response.schema.json` 已更新為多商家購物車設計。
> 金額一律由後端依資料庫計算；前端不得傳送或信任價格、總金額、付款狀態或商品所屬商家。

## 1. 設計前提

| 項目 | 決策 |
| --- | --- |
| 資料庫 | SQLite，使用 Python 標準庫 `sqlite3`，不新增 ORM 依賴 |
| 購物車 | 存資料庫（`carts`／`cart_items`），以 session token 代表目前學生 |
| 身分識別 | Session 模擬：學生用 session token；商家用 `session["merchant_id"]`，提供簡易商家切換 |
| 商品識別 | `products.id` 全域唯一；`merchant_id` 由後端查 `products` 取得 |
| 重複結帳 | `checkout_batches` + `idempotency_key`，同一 session + key 只建立一次訂單 |
| 庫存 | 本階段不實作 |
| 付款 | 建立訂單一律 `unpaid`；模擬付款另外呼叫 `/payment/mock` |

## 2. 路由

| 功能 | Method | 暫定路徑 | 輸入 | 成功回應 | 錯誤情況 |
| --- | --- | --- | --- | --- | --- |
| 商品菜單 | GET | `/menu` | 無 | 200 `menu.html`（`products`） | 後端錯誤 |
| 購物車 | GET | `/cart` | 無 | 200 `cart.html`（`merchant_groups`、`total`） | 後端錯誤 |
| 加入購物車 | POST | `/cart/add` | `product_id`、`quantity` | 重新導向 `/cart` 或 `/menu`，Flash 成功訊息 | 商品不存在、已下架、數量 < 1 |
| 更新購物車 | POST | `/cart/update` | `product_id`、`quantity` | 重新導向 `/cart` | 數量 < 1、商品不存在、商品已下架 |
| 移除購物車項目 | POST | `/cart/remove` | `product_id` | 重新導向 `/cart` | 商品不存在 |
| 結帳頁 | GET | `/checkout` | 無 | 200 `checkout.html`（`merchant_groups`、`total`、`idempotency_key`） | 空購物車 |
| 建立訂單 | POST | `/orders/create` | `idempotency_key` | 依商家建立多張訂單，重新導向結果頁或 `/checkout`，Flash 成功訊息；回傳 `orders[]` | 空購物車、商品已下架、交易失敗；重複 key 回傳既有訂單 |
| 模擬付款 | POST | `/payment/mock` | `order_id` | 更新單張訂單，重新導向結果頁 | 訂單不存在、非目前學生擁有、已付款、付款失敗 |
| 商家商品管理 | GET | `/merchant/products` | 無（商家由 session 決定） | 200 `merchant.html`（`products`） | 未選擇商家、後端錯誤 |
| 新增商品 | POST | `/merchant/products` | `name`、`price` | 重新導向 `/merchant/products`，Flash 成功訊息 | 名稱空白、價格非正數、未選擇商家 |
| 商家訂單列表 | GET | `/merchant/orders` | 無（商家由 session 決定） | 200 `orders.html`（`orders`，僅目前商家） | 未選擇商家、後端錯誤 |

重要限制：

- `/cart/add`、`/cart/update`、`/cart/remove` 不接受前端傳入 `merchant_id`；後端一律由 `product_id` 查詢 `products.merchant_id`。
- `/orders/create` 不接受前端指定商家或金額；後端依購物車商品的 `merchant_id` 分組。
- `/merchant/products`、`/merchant/orders` 的商家範圍由 session 決定，不接受 query string 或表單傳入的 `merchant_id`。
- `products.id` 為全域唯一主鍵，因此購物車操作只需要 `product_id`。

## 3. 模板變數

| 模板 | 變數 | 型別 | 說明 |
| --- | --- | --- | --- |
| `menu.html` | `products` | list[Product] | 上架商品列表，含 `merchant_id`、`merchant_name` |
| `cart.html` | `merchant_groups` | list[MerchantGroup] | 購物車依商家分組後的內容 |
| `cart.html` | `total` | int | 所有商家項目的總額（後端計算） |
| `checkout.html` | `merchant_groups` | list[MerchantGroup] | 結帳預覽，依商家分組 |
| `checkout.html` | `total` | int | 所有商家訂單總額（後端計算） |
| `checkout.html` | `idempotency_key` | str | 本次結帳冪等鍵，需放在送出表單的 hidden 欄位 |
| `checkout.html` | `orders` | list[Order] \| None | 選用；已建立訂單時顯示多張訂單與付款按鈕 |
| `merchant.html` | `products` | list[Product] | 目前商家的商品列表（含未上架） |
| `orders.html` | `orders` | list[Order] | 目前商家的訂單列表 |

## 4. 資料欄位

### MerchantGroup

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `merchant_id` | int | 商家識別碼 |
| `merchant_name` | str | 商家名稱 |
| `items` | list[CartItem] | 此商家的購物車項目 |
| `subtotal` | int | 此商家小計，等於 `items[].subtotal` 加總 |

### Product

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `id` | int | 商品識別碼（全域唯一） |
| `merchant_id` | int | 商品所屬商家 |
| `merchant_name` | str \| None | 商家名稱（由 merchants JOIN 取得，方便顯示） |
| `name` | str | 商品名稱；不同商家可能有相同名稱 |
| `price` | int | 單價（整數新台幣） |
| `image_url` | str \| None | 圖片網址，無圖時使用佔位區塊 |
| `is_available` | bool | 是否上架 |

### CartItem

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `merchant_id` | int | 商品所屬商家；由 `products` 取得，不信任前端 |
| `product_id` | int | 商品識別碼 |
| `name` | str | 商品名稱 |
| `unit_price` | int | 單價（由資料庫提供） |
| `quantity` | int | 數量（>= 1） |
| `subtotal` | int | `unit_price * quantity` |

### Order

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `order_id` | int | 訂單編號 |
| `merchant_id` | int | 訂單所屬商家；一張訂單只能有一個商家 |
| `merchant_name` | str \| None | 商家名稱（方便顯示） |
| `created_at` | datetime \| str | 建立時間 |
| `items` | list[OrderItem] | 此商家訂單的明細 |
| `total` | int | 此商家訂單總額（後端計算） |
| `payment_status` | str | `unpaid` 或 `paid` |

### OrderItem

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `product_id` | int | 商品識別碼 |
| `name` | str | 商品名稱快照，保留建立訂單當下的名稱 |
| `unit_price` | int | 單價快照，保留建立訂單當下的價格 |
| `quantity` | int | 數量 |
| `subtotal` | int | 小計（`unit_price * quantity`） |

## 5. 多商家結帳交易流程

`POST /orders/create` 必須在同一個資料庫 Transaction 內完成：

1. 依目前 session 取得購物車與所有 `cart_items`。
2. JOIN `products` 取得每筆商品的 `merchant_id`、`name`、`price`、`is_available`。
3. 驗證所有商品存在且仍可購買；本階段不做庫存檢查。
4. 依 `products.merchant_id` 將購物車項目分組。
5. 每個商家以資料庫價格重新計算 `subtotal` 與該商家訂單 `total`。
6. 建立一筆 `checkout_batches`，寫入 `idempotency_key`。
7. 為每個商家建立一張 `orders`（`payment_status = 'unpaid'`）與對應的 `order_items` 快照。
8. 全部成功後清空該購物車的 `cart_items`，再 Commit。
9. 任一驗證或寫入失敗時 Rollback，購物車內容保持不變，不留下部分訂單。

重複結帳處理：

- `checkout_batches` 對 `(session_token, idempotency_key)` 建立唯一鍵。
- 若同一 key 再次送出，直接讀取該批次已建立的訂單並回傳，`replayed = true`，不建立新訂單。
- 可使用 SQLite `BEGIN IMMEDIATE` 降低並發寫入衝突。

付款流程：

- 建立訂單時一律 `unpaid`，不可在建立訂單時假設付款成功。
- `POST /payment/mock` 一次只更新一張 `order_id`，且訂單必須屬於目前 session 的學生。
- 已付款訂單不可重複付款。

## 6. Session 模擬身分（Demo）

- 學生：第一次進入網站時建立 `session["cart_token"]`（例如 UUID），`carts`、`orders`、`checkout_batches` 以此 token 歸屬使用者。
- 商家：`session["merchant_id"]` 代表目前商家；提供簡易商家切換（Demo 用），不可用 query string 或表單任意指定要查詢的商家。
- 這是展示用機制，不是正式登入；正式上線應改為真正的帳號與權限驗證。

## 7. 共用規則

- 購物車可同時包含不同商家的商品。
- 每個商品必須有 `merchant_id`，但 `merchant_id` 只能由後端依 `products` 取得。
- 一張訂單只能屬於一個商家；一次結帳可產生多張訂單。
- 不同商家的訂單必須分別計算小計與總金額。
- 所有價格與金額由後端依資料庫計算；不接受瀏覽器傳回的價格或總額。
- `OrderItem.name`、`OrderItem.unit_price` 必須保留建立訂單當下的快照。
- 建立多張訂單必須使用資料庫 Transaction，失敗時全部回滾。
- 訂單建立與付款分開處理；付款狀態只由後端付款路由更新。
- `GET /merchant/orders` 只能回傳目前 session 商家的訂單。
- Flash message 類別沿用 Bootstrap：`success`、`danger`、`warning`、`info`。
- 錯誤訊息以使用者可理解的中文顯示，不輸出後端堆疊。
- 若啟用 CSRF，所有 POST 表單需帶入對應 token；UI 會依後端設定調整。
- 付款流程明確標示「模擬付款／測試流程」。

## 8. 已確認設計決策

- [x] SQLite + Python `sqlite3`。
- [x] 購物車存資料庫。
- [x] Session 模擬學生與商家身分。
- [x] `checkout_batches` + `idempotency_key` 防止重複結帳。
- [x] 本階段不實作庫存。
- [x] 商品 ID 全域唯一，`merchant_id` 由後端查詢。
- [x] 一次結帳依商家建立多張訂單，全部成功才清空購物車。

## 9. 待實作清單

- [ ] 建立 SQLite schema、seed 商家與商品。
- [ ] 實作 `db.py`、購物車／訂單／付款 Service。
- [ ] 將 `app.py` 的骨架路由接上 Service 與 session 身分。
- [ ] 更新 `menu.html`、`cart.html`、`checkout.html`、`merchant.html`、`orders.html`。
- [ ] 更新 request／response JSON Schema 與本契約（本次已完成）。
- [ ] 加入多商家分組、金額、交易回滾、重複結帳、商家權限測試。
- [ ] 確認商家切換 UI 的呈現方式。
