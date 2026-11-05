# COS 校園點餐系統

三人一週 Agile + AI 專題的最小共用骨架。暫定採 Flask、Jinja2、SQLite、本機單一商家且不含登入；模擬付款形式仍待團隊／老師確認，禁止公開部署或串接真實金流。

## Windows PowerShell 快速開始

在 Repository 根目錄執行（不必啟用 `Activate.ps1`）：

```powershell
py --version
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m flask --app backend.app init-db
.\.venv\Scripts\python.exe -m backend.seed
.\.venv\Scripts\python.exe run.py
```

若沒有 `py`，將 `py` 改為 `python`。`init-db` 不清除既有資料。服務只監聽 `127.0.0.1:5000`。

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
Invoke-RestMethod http://127.0.0.1:5000/api/products
.\.venv\Scripts\python.exe -m pytest -q
```

新增商品：

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/products -ContentType 'application/json' -Body '{"name":"雞腿便當","price":85}'
```

## 結構與分工

- `backend/`、`run.py`：C 負責 Flask、SQLite、共用 API。
- `frontend/templates/student/`：A 負責學生菜單、購物車、結帳。
- `frontend/templates/merchant/`：B 負責商品與訂單管理。
- `integration/`：共同維護 API 契約、測試、UML、Agile／AI 證據。
- `instance/`：本機資料庫（Git 忽略）。

已完成 health、商品查詢／新增、DB 初始化與 seed。訂單建立、查詢、模擬付款目前回傳 501；A/B 頁面刻意只留骨架。完整 API 見 `integration/api-contract.md`。
