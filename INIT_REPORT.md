# COS 初始化實際執行報告

## 開始前狀態

- 當時 branch：`Backend`（追蹤 `origin/Backend`），因此未切換或建立 branch。
- 原有檔案：簡短 `README.md`、Python 通用 `.gitignore`、未追蹤的 `Backend/app.py`（空檔）、`Backend/models.py`、`Backend/schema.sql`、既有 `.venv/`。
- 未提交既存修改：`Backend/` 全部未追蹤；視為組員成果保留並沿用，僅將目錄大小寫正規化為跨平台可 import 的 `backend/`。
- 未發現 `Campus_Ordering_Agile_AI_Handoff.md` 或 `Midterm_Project_2026.pdf`。

## 實際建立／移動／修改的檔案

- `Backend/` → `backend/`：只正規化大小寫；保留原 schema 與 sqlite3／Flask context 設計。
- `backend/models.py`：修正 DB 到 repo 根目錄 `instance/`，支援測試覆寫路徑、參數化查詢、commit／rollback。
- `backend/schema.sql`：保留三表與關聯，補強 integer 型別檢查。
- `backend/app.py`、`seed.py`、`__init__.py`、`run.py`：單一 Flask app、CLI、可重複 seed、唯一啟動入口。
- `frontend/`：新增 A/B 五個清楚標記 TODO 的模板骨架與共用 CSS，未代做完整 UI。
- `integration/`：新增 API 契約、19 項隔離測試、Class UML 草稿、分工、Stories、Issues 草稿及空白 Agile／AI 模板。
- `requirements*.txt`、`pytest.ini`：最小依賴與隔離測試設定。
- `README.md`：Windows 安裝、初始化、啟動、測試、API 範例與分工。
- `.gitignore`：補齊 `.venv/`、DB 與測試暫存排除；未移除既有規則。

## 實際執行的指令與結果

| 指令 | Pass / Fail / Not Run | 證據摘要／錯誤 |
|---|---|---|
| `Get-Location`、Git／檔案盤點、`py --version` | Pass | Repo 正確；branch `Backend`；Python 3.13.5 |
| `.venv` 匯入 Flask／pytest | Fail（已修正） | Flask 已存在，pytest 缺少 |
| sandbox 內 `pip install -r requirements-dev.txt` | Fail（已修正） | 受限網路找不到 pytest |
| 經允許下載 pytest | Pass | 安裝 pytest 9.2.0 與最小相依套件 |
| 首輪 `pytest -q` | Fail（環境） | 19 項 setup 均因沙箱拒絕 `%TEMP%`，無應用斷言失敗 |
| sandbox 內改用 `.test-tmp` 重跑 | Fail（環境） | 沙箱仍拒絕其建立的目錄 |
| 沙箱外 `.venv\\Scripts\\python.exe -m pytest -q` | Pass | **19 passed in 0.99s** |
| `flask --app backend.app init-db` | Pass | 非破壞性初始化成功 |
| `python -m backend.seed` 執行兩次 | Pass | 兩次成功，未重複預設商品 |
| SQLite 只讀查核 | Pass | `products`、`orders`、`order_items` 存在；兩筆 seed 商品 |
| 啟動實體開發伺服器／Invoke-RestMethod | Not Run | 已用 Flask test client 覆蓋路由；避免留下背景服務 |

## 可供 A 立即開始

- 修改 `frontend/templates/student/menu.html`，串 `GET /api/products`。
- 完成 cart 數量／移除／小計及 195 元驗收案例。
- 準備 checkout payload，但等待 C 完成 orders API。
- 審核 Stories 並建立 `integration/uml/use-case.puml`；AI 不代簽 PO。

## 可供 B 立即開始

- 修改商家 templates，串 `GET/POST /api/products` 並呈現 400 錯誤。
- 依 `issues-to-create.md` 人工建立 Issues／Projects，留下真實 Daily 紀錄。
- 等待 C 的訂單查詢 API並建立 `activity.puml`。

## 可供 C 立即開始

- 既有 health、商品 API、三表、外鍵、seed 與隔離測試可直接擴充。
- 實作 US05：後端重算、單一 transaction、起始 unpaid。
- 確認模擬付款形式後實作 US06；再完成 US07 查詢與測試。

## 待三人或老師確認

- Flask／Jinja2／SQLite、本機單商家、無登入及 7 天 Sprint 是否採用。
- 是否接受模擬付款，以及成功／失敗／重送的正式規格。
- 是否需要登入、多商家或部署；目前不得公開上線。
- User Stories、Class UML 與 Sprint 範圍仍待 PO／全員審核。

## 未完成與風險

- US05／US06／US07 尚未實作；占位 API 明確回 501。
- A/B UI、Use Case／Activity UML 尚待負責人完成。
- 本次沒有建立遠端看板、Issue、PR，也沒有虛構會議／核准紀錄。
- schema 已可安全初始化，但未建立 migration 機制；日後改 schema 需人工審查。

## Git 狀態與下一個人工動作

- 最終仍在 `Backend` branch；包含已修改 README／gitignore 與新增的初始化檔案，均未 commit。
- 已 commit／push：**否／否**；未 merge、未開 PR、未建立遠端 Issue。
- 建議 C 先審查後端與測試、A/B 審查契約與骨架，再由組員決定如何分支／commit／開 PR；B 人工建立 Projects／Issues，A 做 PO 審核。
