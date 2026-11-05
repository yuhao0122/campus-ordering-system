# COS API 契約

共同規則：JSON；商品 `id`、TWD 價格與數量皆為 integer，價格／數量須為正整數；付款狀態只允許 `unpaid`、`paid`、`failed`。路由或欄位變更需 A/B/C 共同同意。商家端及測試付款無驗證，只能用於受控本機 Demo。

## 已實作

- GET `/health` → 200 `{"status":"ok"}`。
- GET `/api/products` → 200 原始陣列，如 `[{"id":1,"name":"雞腿便當","price":85}]`，無資料為 `[]`。
- POST `/api/products`，Content-Type `application/json`，請求 `{"name":"雞腿便當","price":85}`；成功 201 並持久化相同欄位；非法輸入 400 `{"error":{"code":"invalid_input","message":"..."}}`。空白名稱及非正整數（含 bool）價格非法。

## 待實作（占位均回 501 `not_implemented`）

- POST `/api/orders`（C；A UI）：預定請求 `{"items":[{"product_id":1,"quantity":2}]}`；後端查 DB 單價、同一交易寫訂單／明細、起始 unpaid；不信任前端金額。
- GET `/api/orders`（C；B UI）：預定回訂單、明細、後端總額、時間與付款狀態。
- POST `/api/orders/<order_id>/simulate-payment`（C；A UI）：形式待核准；成功才持久化 paid，失敗不得誤設 paid，重送需安全。

驗收案例：2 個 85 元雞腿便當 + 1 杯 25 元紅茶 = 195 元，正式總額由後端重算。
