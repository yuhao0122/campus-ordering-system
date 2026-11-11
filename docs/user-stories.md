# COS 校園點餐系統 User Stories

> 依據目前程式碼（Flask + SQLite + Jinja2 SSR）與 Git 提交紀錄整理。
> 本文件是對 `integration/docs/user-stories.md` 草稿的正式化與擴充版本；狀態以目前 `main` 分支實作為準。
> 系統為本機 Demo，付款僅為模擬流程，不可用於真實金流。

## 1. 文件目的與範圍

- 以「角色 → 目標 → 價值」描述目前已實作的功能，並補上尚未實作但已在歷史紀錄中出現的需求。
- 每則 Story 附上驗收條件、實作對應（路由／函式／模板／測試）與 Git 證據，方便追溯。
- 涵蓋角色：學生（Student）、商家（Merchant）、系統維護者（Developer／Demo 操作者）。

## 2. 角色定義

| 角色 | 說明 | 目前身分模擬方式 |
| --- | --- | --- |
| 學生 | 瀏覽菜單、管理購物車、結帳、模擬付款 | `session["cart_token"]`（UUID） |
| 商家 | 管理商品、查看訂單 | `session["merchant_id"]`，可經 `/merchant/select` 切換 |
| 維護者 | 初始化資料庫、seed、執行測試 | CLI 指令與 pytest |

## 3. Git 歷程與功能演進

| 日期 | Commit | 內容 | 對應 Story |
| --- | --- | --- | --- |
| 2026-11-04 | `a7b352e` | Initial commit | 專案基礎 |
| 2026-11-05 | `71e47d3` | 建立 Flask UI 頁面骨架、UI 契約與 backlog | US-01～US-10 的 UI 基礎 |
| 2026-11-05 | `fef5f2c` | 初始化後端：schema、models、seed、pytest、整合文件 | US-08、US-11、US-13 |
| 2026-11-05 | `16ed78b` | Merge PR #1（Backend） | 後端基礎進主線 |
| 2026-11-07 | `134e5e9` | 更新多商家購物車 UI 契約 | US-04、US-10 |
| 2026-11-09 | `25f3df8` | Merge FrontUI | UI 契約進主線 |
| 2026-11-09 | `065ad7b` | 新增 SSR 點餐 UI 整合契約、購物車金額試算、訂單摘要 partial | US-02、US-03、US-06 |
| 2026-11-10 | `9fd75c6` | 整合前端與後端訂購流程：多商家購物車、交易式建單、冪等、付款、商家隔離、migration | US-04～US-12 |
| 2026-11-10 | `e7ac4c6`、`d32e6e7` | Merge FrontUI／Backend，形成目前 `main` | 全部 |

主要分支：`Backend`（後端與資料層）、`FrontUI`（樣板與整合契約）、`flask_fix`／`main`（整合結果）。

## 4. Story 總覽

| ID | Epic | Story | 角色 | 優先級 | 狀態 |
| --- | --- | --- | --- | --- | --- |
| US-01 | 學生點餐 | 瀏覽商品菜單 | 學生 | Must | 已實作 |
| US-02 | 學生點餐 | 將商品加入購物車 | 學生 | Must | 已實作 |
| US-03 | 學生點餐 | 調整數量與移除購物車商品 | 學生 | Must | 已實作 |
| US-04 | 學生點餐 | 以商家分組檢視購物車與總額 | 學生 | Must | 已實作 |
| US-05 | 學生點餐 | 確認結帳並建立訂單 | 學生 | Must | 已實作 |
| US-06 | 學生點餐 | 進行模擬付款 | 學生 | Must | 已實作 |
| US-07 | 學生點餐 | 防止重複送出訂單 | 學生／系統 | Must | 已實作 |
| US-08 | 商家管理 | 新增商品 | 商家 | Must | 已實作 |
| US-09 | 商家管理 | 僅管理自己商家的商品 | 商家 | Should | 已實作 |
| US-10 | 商家管理 | 查看所有商家訂單總覽 | 商家 | Should | 已實作（Demo 範圍） |
| US-11 | 平台維運 | 初始化與建立示範資料 | 維護者 | Must | 已實作 |
| US-12 | 平台維運 | 升級舊版資料庫並保留資料 | 維護者 | Should | 已實作 |
| US-13 | 平台維運 | 健康檢查 | 維護者 | Could | 已實作 |
| US-14 | 平台維運 | 隔離不同學生的購物車與訂單 | 系統 | Must | 已實作 |
| US-B1 | 商家管理 | 切換目前商家（UI） | 商家 | Could | 部分實作（僅路由） |
| US-B2 | 學生點餐 | 正式登入與權限 | 全體 | Won't（本階段） | 未實作 |
| US-B3 | 商家管理 | 商品編輯／下架／庫存 | 商家 | Won't（本階段） | 未實作 |
| US-B4 | 平台維運 | CSRF 防護 | 系統 | Won't（本階段） | 未實作 |

優先級採 MoSCoW：Must／Should／Could／Won't（本階段）。

---

## 5. Epic A：學生點餐

### US-01 瀏覽商品菜單

**身為**學生，**我想要**看到目前所有商家的上架商品、價格與商家名稱，**以便**決定要買什麼。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `GET /menu` 由後端傳入 `products`，頁面不寫死商品資料。
- [x] 每張商品卡顯示名稱、`NT$` 價格、商品描述；無圖片時顯示一致佔位區塊。
- [x] 商品顯示所屬商家名稱。
- [x] 已下架商品顯示「已下架」，不提供加入購物車表單。
- [x] 無商品時顯示「目前沒有上架商品」空狀態。
- [x] 商品清單由 `products JOIN merchants` 取得，包含 `merchant_id`、`merchant_name`。

**實作對應**：`backend/app.py:61`（`menu`）、`backend/models.py:93`（`list_products`）、`templates/menu.html`
**測試**：`test_seed_idempotent_and_menu_renders_data`

---

### US-02 將商品加入購物車

**身為**學生，**我想要**選擇數量並把商品加入購物車，**以便**一次選購多樣商品。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `POST /cart/add` 只接受 `product_id`、`quantity`。
- [x] 數量必須是嚴格正整數；`0`、負數、小數、空字串、非數字皆拒絕並提示「格式不正確」。
- [x] 商品不存在或已下架時顯示可理解的中文錯誤。
- [x] 同一商品重複加入會累加數量，而非新增重複列。
- [x] 成功後顯示「已加入購物車」Flash 並導回菜單。
- [x] 加入成功會清除舊的 `session["checkout_key"]`，避免沿用過期冪等鍵。
- [x] 商品所屬商家由後端查詢，不接受前端傳入 `merchant_id`。

**實作對應**：`backend/app.py:70`（`add_to_cart`）、`backend/models.py:127`（`add_cart_item`）、`templates/menu.html`
**測試**：`test_add_accumulates_and_cart_context_is_complete`、`test_invalid_quantity_is_rejected`

---

### US-03 調整數量與移除購物車商品

**身為**學生，**我想要**在購物車調整數量或移除商品，**以便**確認最後要買的內容。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `GET /cart` 顯示每筆商品名稱、單價、數量、小計與移除操作。
- [x] `POST /cart/update` 更新數量，僅接受正整數；非法值提示改用移除。
- [x] 更新時若商品已下架，拒絕更新並提示。
- [x] `POST /cart/remove` 可移除指定商品；不存在時顯示提示。
- [x] 數量變更後，前端即時更新單列小計、各商家小計與總額。
- [x] 空購物車顯示「購物車是空的」與前往菜單連結。
- [x] 前端金額僅供預覽，正式金額由後端重新計算。

**實作對應**：`backend/app.py:86`、`backend/app.py:100`、`backend/models.py:143`、`backend/models.py:162`、`templates/cart.html`、`static/js/cart.js`
**測試**：`test_update_and_remove_cart`、`test_update_rejects_unavailable_product`、`test_empty_cart_and_checkout_states`

---

### US-04 以商家分組檢視購物車與總額

**身為**學生，**我想要**在購物車看到不同商家商品的分組與各自小計，**以便**了解一次結帳會產生多張訂單。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] 購物車可同時包含多個商家的商品。
- [x] 後端依 `products.merchant_id` 分組，回傳 `merchant_groups` 與 `total`。
- [x] 每個商家群組包含 `merchant_id`、`merchant_name`、`items`、`subtotal`。
- [x] 每筆項目包含 `unit_price`、`quantity`、`subtotal`，金額皆由資料庫計算。
- [x] 總額等於所有商家小計加總。
- [x] 前端不得傳送或覆寫價格、總額或商家。

**實作對應**：`backend/models.py:170`（`get_cart_groups`）、`templates/cart.html`、`templates/partials/order_summary.html`
**測試**：`test_add_accumulates_and_cart_context_is_complete`、`test_multi_merchant_order_snapshot_total_and_idempotency`

---

### US-05 確認結帳並建立訂單

**身為**學生，**我想要**在結帳頁確認訂單摘要後送出訂單，**以便**完成點餐。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `GET /checkout` 顯示依商家分組的訂單摘要與後端計算的總額。
- [x] 結帳頁明確標示「模擬付款／測試流程」。
- [x] 有購物車內容時產生並帶入 hidden `idempotency_key`。
- [x] `POST /orders/create` 只接受 `idempotency_key`，不接受商家或金額。
- [x] 後端在單一交易內驗證購物車非空、商品皆上架。
- [x] 依商家各建立一張 `orders`，並寫入 `order_items` 的商品名稱與單價快照。
- [x] 每張新訂單 `payment_status = 'unpaid'`。
- [x] 全部成功後清空購物車；任何錯誤則 Rollback，購物車保持不變。
- [x] 成功後顯示「訂單已建立」並顯示訂單與付款按鈕。
- [x] 空購物車顯示「目前沒有可結帳的商品」。

**實作對應**：`backend/app.py:109`、`backend/app.py:123`、`backend/models.py:188`（`create_orders_from_cart`）、`templates/checkout.html`
**測試**：`test_multi_merchant_order_snapshot_total_and_idempotency`、`test_checkout_rolls_back_when_product_unavailable`、`test_empty_cart_and_checkout_states`

---

### US-06 進行模擬付款

**身為**學生，**我想要**對已建立的訂單進行模擬付款，**以便**完成 Demo 流程。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `POST /payment/mock` 只接受 `order_id`。
- [x] 只能付款屬於目前 session 學生的訂單，否則提示找不到可付款訂單。
- [x] 已付款訂單不可重複付款，重送顯示「已付款」。
- [x] 付款成功將該訂單更新為 `paid` 並顯示成功訊息。
- [x] 付款狀態只由後端路由更新，前端按鈕不能直接改變。
- [x] 一次只更新單張訂單，不影響其他商家訂單。
- [x] 頁面明確標示為模擬付款，不收集真實金流資料。

**實作對應**：`backend/app.py:139`、`backend/models.py:260`（`pay_order`）、`templates/checkout.html`
**測試**：`test_payment_is_owner_only_and_not_repeatable`

---

### US-07 防止重複送出訂單

**身為**學生或系統，**我想要**在網路重送或連點時不重複建立訂單，**以便**避免重複下單。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `checkout_batches` 對 `(session_token, idempotency_key)` 建立唯一鍵。
- [x] 同一 session + key 再次送出時，直接回傳既有批次，顯示「未重複送出」。
- [x] 表單 key 與 session key 不符時視為過期，重新導向結帳頁。
- [x] 使用 `BEGIN IMMEDIATE` 降低並發寫入衝突。
- [x] 重送不會新增訂單或重複扣減購物車。

**實作對應**：`backend/app.py:126`、`backend/models.py:192`、`backend/schema.sql:35`、`templates/checkout.html`
**測試**：`test_multi_merchant_order_snapshot_total_and_idempotency`

---

## 6. Epic B：商家管理

### US-08 新增商品

**身為**商家，**我想要**新增商品名稱與價格，**以便**讓學生選購。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `GET /merchant/products` 顯示目前商家的商品列表（含未上架）。
- [x] 表單包含可見標籤的商品名稱與價格欄位。
- [x] `POST /merchant/products` 驗證名稱不可空白、價格為正整數。
- [x] 驗證失敗顯示中文錯誤訊息，不建立商品。
- [x] 成功後顯示「商品新增成功」並更新列表。
- [x] 新增商品會歸屬於目前 session 的商家。

**實作對應**：`backend/app.py:158`、`backend/app.py:167`、`backend/models.py:108`（`create_product`）、`templates/merchant.html`
**測試**：`test_merchant_data_is_isolated`（間接涵蓋商家範圍）

---

### US-09 僅管理自己商家的商品

**身為**商家，**我想要**只看到並管理自己商家的商品，**以便**避免誤改其他商家資料。

**優先級**：Should　**狀態**：已實作

**驗收條件**

- [x] 商家範圍由 `session["merchant_id"]` 決定，不接受 query string 任意指定。
- [x] `GET /merchant/products` 只回傳該商家的商品。
- [x] 切換商家後，商品列表隨之改變。
- [x] `POST /merchant/products` 一律建立於目前商家。

**實作對應**：`backend/app.py:152`、`backend/models.py:101`（`list_products_by_merchant`）
**測試**：`test_merchant_data_is_isolated`

---

### US-10 查看所有商家訂單總覽

**身為**商家，**我想要**查看所有商家的學生訂單、商品、金額與付款狀態，**以便**掌握出餐與收款（本機 Demo 範圍）。

**優先級**：Should　**狀態**：已實作（Demo 專用）

**驗收條件**

- [x] `GET /merchant/orders` 顯示所有商家訂單，每筆標示商家名稱。
- [x] 每筆訂單顯示訂單編號、商品及數量、總金額、付款狀態、建立時間。
- [x] 已付款與未付款以不同樣式區分。
- [x] 金額直接使用後端資料，不由頁面重新計算。
- [x] 無訂單時顯示「目前沒有訂單」空狀態。
- [x] 頁面明確標示為「查看所有商家的學生訂單」。

**實作對應**：`backend/app.py:181`、`backend/models.py:240`（`list_orders`）、`templates/orders.html`
**測試**：`test_merchant_orders_renders_all_merchants`

---

### US-B1 切換目前商家（UI）

**身為**商家，**我想要**在畫面上切換目前操作的商家，**以便**管理不同商家的商品。

**優先級**：Could　**狀態**：部分實作

**驗收條件**

- [x] `POST /merchant/select` 接受 `merchant_id`，只允許資料庫存在的商家。
- [x] 切換成功後導向商家商品頁並顯示提示。
- [ ] 前端提供可見的商家切換控制（README 註明可後續討論，目前尚無 UI）。

**實作對應**：`backend/app.py:185`
**備註**：後端路由已存在，前端控制項尚未實作。

---

## 7. Epic C：平台維運與跨角色

### US-11 初始化與建立示範資料

**身為**維護者，**我想要**安全地初始化資料庫並建立示範商家／商品，**以便**快速啟動 Demo。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] `flask --app app init-db` 建立 schema 且不刪除既有資料。
- [x] `init-db` 偵測到舊版 schema 時拒絕執行並提示先 migration。
- [x] `python -m backend.seed` 可重複執行，不重複新增商家或商品。
- [x] 預設建立「校園食堂」「飲料店」與 4 個商品。

**實作對應**：`backend/app.py:43`、`backend/models.py:31`、`backend/seed.py`
**測試**：`test_health_schema_foreign_keys_and_idempotent_init`、`test_seed_idempotent_and_menu_renders_data`

---

### US-12 升級舊版資料庫並保留資料

**身為**維護者，**我想要**把舊版單商家資料庫升級為多商家 schema，**以便**保留既有商品與訂單。

**優先級**：Should　**狀態**：已實作

**驗收條件**

- [x] `flask --app app migrate-db` 在交易內改名舊表、建立新 schema。
- [x] 舊商品自動歸屬到預設商家「校園食堂」。
- [x] 舊訂單與訂單明細一併搬移並補上商家與商品名稱快照。
- [x] 成功後刪除 legacy 表；失敗則 Rollback。
- [x] 已是最新版時不重複 migration。

**實作對應**：`backend/app.py:48`、`backend/models.py:39`（`migrate_legacy_db`）
**測試**：`test_legacy_database_migration_preserves_products`

---

### US-13 健康檢查

**身為**維護者，**我想要**有一個輕量健康檢查端點，**以便**確認服務是否啟動。

**優先級**：Could　**狀態**：已實作

**驗收條件**

- [x] `GET /health` 回傳 `{"status": "ok"}`。
- [x] 不需登入即可使用，僅供診斷。

**實作對應**：`backend/app.py:57`
**測試**：`test_health_schema_foreign_keys_and_idempotent_init`

---

### US-14 隔離不同學生的購物車與訂單

**身為**系統，**我想要**以 session token 隔離學生資料，**以便**避免學生看到或操作他人的購物車與訂單。

**優先級**：Must　**狀態**：已實作

**驗收條件**

- [x] 每位學生以 `session["cart_token"]` 對應獨立的 `carts`。
- [x] 購物車、訂單、結帳批次皆以 session token 歸屬。
- [x] 付款時驗證訂單所有權，他人訂單不可付款。
- [x] Demo 首次請求自動建立 token 與預設商家。

**實作對應**：`backend/app.py:32`（`ensure_demo_identity`）、`backend/models.py:121`、`backend/models.py:262`
**測試**：`test_payment_is_owner_only_and_not_repeatable`

---

## 8. 尚未實作 / 本階段排除（Backlog）

以下項目在 Git 歷史或文件中被提及，但目前不在系統功能內，列為後續 Story。

| ID | Story | 說明 | 優先級 |
| --- | --- | --- | --- |
| US-B2 | 正式登入與權限 | 以真正帳號／角色驗證取代 session 模擬 | Won't（本階段） |
| US-B3 | 商品編輯、下架與庫存 | 目前僅新增商品，無編輯／刪除／庫存管理 | Won't（本階段） |
| US-B4 | CSRF 防護 | 目前 POST 表單未帶 CSRF token | Won't（本階段） |
| US-B5 | 真實金流 | 目前僅 `/payment/mock` 模擬付款 | Won't（本階段） |
| US-B6 | JSON API | 目前為 SSR，無 `/api/*` 資料路由 | Could |
| US-B7 | 前端商家切換控制 | 後端路由已存在，UI 尚未提供 | Could |
| US-B8 | 商品圖片上傳 | schema 有 `image_url`，目前僅支援外部網址或佔位圖 | Could |

## 9. 驗收與測試對應矩陣

| Story | 自動測試 |
| --- | --- |
| US-01 | `test_seed_idempotent_and_menu_renders_data` |
| US-02 | `test_add_accumulates_and_cart_context_is_complete`、`test_invalid_quantity_is_rejected` |
| US-03 | `test_update_and_remove_cart`、`test_update_rejects_unavailable_product`、`test_empty_cart_and_checkout_states` |
| US-04 | `test_add_accumulates_and_cart_context_is_complete`、`test_multi_merchant_order_snapshot_total_and_idempotency` |
| US-05 | `test_multi_merchant_order_snapshot_total_and_idempotency`、`test_checkout_rolls_back_when_product_unavailable` |
| US-06 | `test_payment_is_owner_only_and_not_repeatable` |
| US-07 | `test_multi_merchant_order_snapshot_total_and_idempotency` |
| US-08 | `test_merchant_data_is_isolated`（部分） |
| US-09 | `test_merchant_data_is_isolated` |
| US-10 | `test_merchant_orders_renders_all_merchants` |
| US-11 | `test_health_schema_foreign_keys_and_idempotent_init`、`test_seed_idempotent_and_menu_renders_data` |
| US-12 | `test_legacy_database_migration_preserves_products` |
| US-13 | `test_health_schema_foreign_keys_and_idempotent_init` |
| US-14 | `test_payment_is_owner_only_and_not_repeatable` |

執行測試：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## 10. 非功能需求

| 類別 | 需求 | 目前狀態 |
| --- | --- | --- |
| 金額正確性 | 所有金額由後端依資料庫計算，前端不得信任 | 已達成 |
| 交易一致性 | 多商家建單為單一交易，失敗全部回滾 | 已達成 |
| 冪等性 | 同一結帳 key 不重複建單 | 已達成 |
| 資料隔離 | 學生以 session token 隔離；商家以 `merchant_id` 隔離商品 | 已達成 |
| 快照 | 訂單明細保存下單當下名稱與單價 | 已達成 |
| 錯誤處理 | 預期錯誤使用 `DomainError` 顯示中文；非預期例外寫 log | 已達成 |
| 可測試性 | app factory + 可覆寫 DB 路徑，測試使用獨立 SQLite | 已達成 |
| 安全性 | 無 CSRF、無正式登入，僅適合本機 Demo | 未達成（本階段排除） |

## 11. 相關文件

| 文件 | 說明 |
| --- | --- |
| `README.md` | 啟動方式與路由摘要 |
| `docs/architecture.md` | 系統架構、資料模型與流程 |
| `docs/ui-backend-contract.md` | UI／後端正式契約 |
| `integration/docs/user-stories.md` | 早期 User Story 草稿（本文件的前身） |
| `docs/ui-backlog.md` | 早期 UI 需求與 backlog |
| `integration/tests/test_smoke.py` | 自動化驗收測試 |
