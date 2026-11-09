# UI／後端整合契約入口

本專案 UI 採用 **Flask 伺服器端渲染 + HTML 表單 POST + redirect/Flash**，不是以 JSON API 作為頁面資料來源。

正式且唯一的欄位、endpoint、template context 與交易契約為 [`docs/ui-backend-contract.md`](../docs/ui-backend-contract.md)。本文件只記錄後端實作邊界，避免維護兩份互相矛盾的契約。

## 實作狀態

- 已實作：商品菜單、資料庫購物車、加入／更新／移除、多商家分組與後端計價。
- 已實作：以 `(session_token, idempotency_key)` 防重複的交易式多商家建單。
- 已實作：商品名稱／單價快照、模擬付款所有權檢查、商家商品隔離及全商家訂單總覽。
- 已實作：`init-db`、可重複 seed、保留舊資料的 `migrate-db`。
- `GET /health` 保留為診斷用途；沒有 UI 依賴 `/api/*` JSON 路由。

## 信任邊界

瀏覽器只送 `product_id`、`quantity`、`idempotency_key` 或 `order_id`。價格、總額、商家、session token 與付款狀態一律由後端／session／資料庫決定。模擬付款僅供本機 Demo。
