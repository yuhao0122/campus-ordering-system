# UI / 後端整合契約（草稿）

> 狀態：**待與後端組員確認**。
> 本文件的路由與模板變數是依 `UI_Agent_Work_Spec.md` 提出的暫定介面，不代表後端已完成。
> 確認後請更新此文件，UI 再依最終版本調整；UI 不在前端計算正式金額或改變付款狀態。

## 1. 路由

| 功能 | Method | 暫定路徑 | 輸入 | 成功回應 | 錯誤情況 |
| --- | --- | --- | --- | --- | --- |
| 商品菜單 | GET | `/menu` | 無 | 200 `menu.html`（`products`） | 後端錯誤 |
| 購物車 | GET | `/cart` | 無 | 200 `cart.html`（`cart_items`、`total`） | 後端錯誤 |
| 加入購物車 | POST | `/cart/add` | `product_id`、`quantity` | 重新導向 `/cart` 或 `/menu`，Flash 成功訊息 | 商品不存在、已下架、數量 < 1 |
| 更新購物車 | POST | `/cart/update` | `product_id`、`quantity` | 重新導向 `/cart` | 數量 < 1、商品不存在 |
| 移除購物車項目 | POST | `/cart/remove` | `product_id` | 重新導向 `/cart` | 商品不存在 |
| 結帳頁 | GET | `/checkout` | 無 | 200 `checkout.html`（`cart_items`、`total`） | 空購物車 |
| 建立訂單 | POST | `/orders/create` | 無（以後端購物車為準） | 重新導向付款或結果頁，Flash 成功訊息 | 空購物車、商品已下架 |
| 模擬付款 | POST | `/payment/mock` | `order_id` | 重新導向結果頁，顯示成功與訂單編號 | 訂單不存在、已付款、付款失敗 |
| 商家商品管理 | GET | `/merchant/products` | 無 | 200 `merchant.html`（`products`） | 後端錯誤 |
| 新增商品 | POST | `/merchant/products` | `name`、`price` | 重新導向 `/merchant/products`，Flash 成功訊息 | 名稱空白、價格非正數 |
| 商家訂單列表 | GET | `/merchant/orders` | 無 | 200 `orders.html`（`orders`） | 後端錯誤 |

> 若後端採用不同路徑，請以實際路由為準，並同步更新模板中的 `url_for`。

## 2. 模板變數

| 模板 | 變數 | 型別 | 說明 |
| --- | --- | --- | --- |
| `menu.html` | `products` | list[Product] | 上架商品列表 |
| `cart.html` | `cart_items` | list[CartItem] | 購物車項目 |
| `cart.html` | `total` | int | 購物車總額（後端計算） |
| `checkout.html` | `cart_items` | list[CartItem] | 待結帳項目 |
| `checkout.html` | `total` | int | 訂單總額（後端計算） |
| `checkout.html` | `order` | Order \| None | 已建立訂單（若流程需要） |
| `merchant.html` | `products` | list[Product] | 商家商品列表（含未上架） |
| `orders.html` | `orders` | list[Order] | 商家訂單列表 |

## 3. 資料欄位（暫定）

### Product

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `id` | int | 商品識別碼 |
| `name` | str | 商品名稱 |
| `price` | int | 單價（新台幣） |
| `image_url` | str \| None | 圖片網址，無圖時使用佔位區塊 |
| `is_available` | bool | 是否上架 |

### CartItem

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `product_id` | int | 商品識別碼 |
| `name` | str | 商品名稱 |
| `unit_price` | int | 單價 |
| `quantity` | int | 數量（>= 1） |
| `subtotal` | int | `unit_price * quantity` |

### Order

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `id` | int | 訂單編號 |
| `created_at` | datetime \| str | 建立時間 |
| `items` | list[OrderItem] | 訂單明細 |
| `total` | int | 訂單總額（後端計算） |
| `payment_status` | str | `unpaid` 或 `paid` |

### OrderItem

| 欄位 | 型別 | 說明 |
| --- | --- | --- |
| `name` | str | 商品名稱 |
| `unit_price` | int | 單價 |
| `quantity` | int | 數量 |
| `subtotal` | int | 小計 |

## 4. 共用規則

- 金額一律由後端計算，UI 只呈現；不接受瀏覽器傳回的總金額作為訂單金額。
- 付款狀態只由後端路由更新。
- Flash message 類別沿用 Bootstrap：`success`、`danger`、`warning`、`info`。
- 錯誤訊息以使用者可理解的中文顯示，不輸出後端堆疊。
- 若啟用 CSRF，所有 POST 表單需帶入對應 token；UI 會依後端設定調整。
- 付款流程明確標示「模擬付款／測試流程」。

## 5. 待確認清單

- [ ] 上述路由名稱與 method 是否與後端一致？
- [ ] 購物車是否存在 session 或資料庫？`cart_items` 實際欄位為何？
- [ ] 商品是否有 `image_url`、`is_available` 欄位？
- [ ] 訂單付款狀態值為何？是否使用 `unpaid`／`paid`？
- [ ] 建立訂單後是導向付款頁或直接導向結果頁？
- [ ] 是否使用 Flask-WTF／CSRF？表單 token 欄位名稱？
- [ ] 金額是否為整數新台幣？
- [ ] 後端是否提供訂單編號與建立時間？
