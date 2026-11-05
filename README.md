# 商家端商品及訂單頁面（第四階段 UI 可測試版）

> 此包保留第三階段商品頁功能，新增第四階段「查看學生訂單」頁面。**沒有建立 Flask app.py、db.py 或 SQLite。**

## 檔案清單

```text
templates/
  merchant.html         # 商品新增與商品列表（保留第三階段功能，新增導覽連結）
  merchant_orders.html  # 新增：商家訂單列表、明細、訂單總額及付款狀態
static/
  merchant.js           # 兩頁共用；商品 API + 訂單 API；提供明確的示範模式
docs/agile/
  day5_evidence_template.md
```

## 在 Windows 立即操作（不用 Flask）

### 方式 A：直接雙擊 HTML

直接用瀏覽器打開 `templates/merchant.html`，點「查看學生訂單」。因 `file://` 網址自動判斷為示範模式，所有資料都是暫時的假資料。

### 方式 B：推薦：HTTP 靜態預覽

在本資料夾開 PowerShell：

```powershell
python -m http.server 5500
```

瀏覽器打開：

- 商品：`http://localhost:5500/templates/merchant.html?demo=1`
- 訂單：`http://localhost:5500/templates/merchant_orders.html?demo=1`

示範訂單固定兩筆，分別顯示 `unpaid`／`paid`。這個模式**不讀取 SQLite，也不會改變付款狀態**。可以點「重新整理」重新載入示範清單。

## 正式 API 規格（待 C 的專案骨架）

`GET /api/merchant/orders` 成功：HTTP 200，回傳陣列。例如：

```json
[
  {
    "id": 1001,
    "total_amount": 170,
    "payment_status": "unpaid",
    "created_at": "2026-11-05 11:25:00",
    "items": [
      {"product_name": "雞腿便當", "unit_price": 85, "quantity": 2, "subtotal": 170}
    ]
  }
]
```

- 無訂單回傳 `[]`，前端顯示「目前沒有學生訂單」。
- API 錯誤為 `{"error":"錯誤訊息"}`，前端顯示 API 回報的錯誤，不露出 SQLite 內部例外。
- 付款狀態只接受 `unpaid`、`paid`；商家端只能查看，不會自行標記已付款。
- 現在的 `merchant.js` 會根據 `?demo=1` 或 `file://` 選擇示範資料，否則使用相對於網站根目錄的真實 API。

## 等 C 提供資料庫後，待確認事項

1. C 的 `db.py` 定義與 `get_db()` 回傳連線格式。
2. `orders`、`order_items` 欄位確實符合契約；`created_at` 字串格式由 C 決定。
3. 商家訂單 Blueprint 頁面路由 `/merchant/orders`，及商品頁路由 `/merchant` 是否由 C 註冊。
4. B 在 `routes/merchant.py` 使用 C 的 `get_db()`，不可另外建 DB 或動資料表結構。
5. C/A 建立的測試訂單能否由 `GET /api/merchant/orders` 讀到，並確認 `total_amount` 對應 `items` 的 subtotal。
6. HTML 引用 `../static/merchant.js` 適用 `/merchant`、`/merchant/orders` 與靜態預覽，若 C 使用 Blueprint url_prefix 或不同路徑需一同檢查。

## 人工驗收（執行後才勾選）

- [ ] 靜態預覽可以切換商品頁／訂單頁
- [ ] 訂單頁顯示兩筆明確標示的假資料
- [ ] unpaid 顯示「未付款」；paid 顯示「已付款（模擬）」
- [ ] 商品明細、單價、數量、小計與總額正確
- [ ] 商品新增、輸入驗證仍正常
- [ ] 正式 Flask API 訂單列表有資料顯示正常（待 C）
- [ ] 正式 Flask API 空陣列顯示空狀態（待 C）
- [ ] 正式 Flask API 錯誤會顯示提示（待 C）
- [ ] 審查者實際確認 PR 並記錄意見

## GitHub 建議（尚未實際執行）

- Issue：B-US05、B-US06 先放 In Progress，未與後端整合前不可 Done。
- 建議分支：`feature/merchant-orders`（實際建立時從最新 `main` 開始；若商品頁尚未合併，須先協調合併或合適的分支起點）。
- Commit 標題：`feat(merchant): add order list UI with payment status`
- PR 連結、Review Comment、截圖、人工驗收請填入 `docs/agile/day5_evidence_template.md`。

## 安全範圍

這是單一商家、沒有身分驗證的本機課堂展示介面，不適合公開上線，也不能處理實際付款或個資。
