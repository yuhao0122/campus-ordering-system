# COS 校園點餐系統 AI 對話紀錄總結

> 資料來源：opencode 本機工作階段資料庫（`~\.local\share\opencode\opencode.db`）中屬於本專案的 9 個 session（2026-11-05 ～ 2026-11-11），並對照 git 提交紀錄與目前檔案狀態驗證。
> 產生日期：2026-11-11

## 0. Session 總覽

| # | 日期 | Session 主題 | 主要產出 |
| --- | --- | --- | --- |
| 1 | 11-05 | UI_Agent_Work_Spec 加入 .gitignore；完成 Day 1 / Day 2 | UI Backlog、整合契約草稿、Flask 骨架與頁面、`.venv` |
| 2 | 11-07 | 設計後端 JSON 封包格式 | `docs/api-request.schema.json`、`docs/api-response.schema.json`、多商家契約改版、購物車／付款 UI 調整 |
| 3 | 11-09 | 如何測試目前功能 | 釐清測試與執行方式（`run.py` → `backend.app`） |
| 4 | 11-09 | 後端框架是否使用 Flask | 確認為 Flask + Jinja2 SSR、無 SPA；分析 root `app.py` 僅為骨架 |
| 5 | 11-09 | 根據 ui.md 調整專案架構 | 共用訂單摘要 partial、`cart.js` 即時試算、重寫 menu/cart/checkout、`docs/backend-integration-requirements.md` |
| 6 | 11-09~10 | 查詢目前專案的執行指令 | 執行／初始化／migration／測試指令說明 |
| 7 | 11-10 | 如何查看前後端串接結果 | 執行 `migrate-db` + `seed` 修復本機舊版 DB（500 → 全部 200）、清理佔用 port 5000 的殘留程序 |
| 8 | 11-10 | 架構整理成 .md、產生 user story、UML | `docs/user-stories.md`、`docs/uml/`（use case / class / sequence）；`docs/architecture.md` 曾寫出但目前已不存在 |
| 9 | 11-11 | 建立 GitHub Projects 看板並匯入 User Stories | 僅完成規劃，未執行（本機無 `gh` CLI） |

## 一、主要架構討論

| 主題 | 結論 |
| --- | --- |
| 技術棧 | Flask + Jinja2 SSR（伺服器端渲染）+ SQLite + 原生 JS/CSS，**沒有** Vue/React 等 SPA 框架 |
| 前端要不要自己的 Flask | 不衝突原則：全專案只保留**一個** Flask app，前端只維護 `templates/`、`static/`；本機預覽共用同一 app，不重複定義路由 |
| 整合方案之爭 | 曾比較「Backend JSON API（fetch 動態渲染）」vs「FrontUI SSR（Jinja 變數＋表單 POST）」，最後**採用 SSR 契約**，並產出 `docs/backend-integration-requirements.md` 列出後端需配合的修改（資料傳遞、路由、schema、session 身分、模板位置、endpoint 命名、CSRF 等） |
| 多商家購物車（核心設計） | 一次結帳依 `merchant_id` 分組，**每商家各建立一張訂單**；金額一律由後端依資料庫計算、不信任前端；`merchant_id` 由後端查詢（request schema 因此移除前端傳入）；`idempotency_key` 冪等防重複下單；單一交易（`BEGIN IMMEDIATE`）、失敗全部 rollback；訂單明細保存商品名稱／單價快照 |
| 資料庫演進 | 舊 schema（products / orders / order_items）→ 新增 `merchants`、`carts`、`cart_items`、`checkout_batches`；`products` 擴充 `merchant_id`、`description`、`image_url`、`is_available`；`migrate-db` 於交易內升級並保留舊資料 |
| API 封包設計 | `docs/api-request.schema.json`、`docs/api-response.schema.json`：統一 `success / data / error / meta` 封包、`merchant_groups` 分組、`OrderItem` 快照；商品以 `merchant_id + product_id` 識別（不同商家可能有同名商品） |
| 身分模型 | Demo 階段以 session 模擬：學生用 `session["cart_token"]`（UUID）、商家用 `session["merchant_id"]`；無正式登入（列為 Backlog） |

## 二、功能修改歷程（依時間與 commit 對應）

| 日期 | Session | 實際修改內容 | Git 對應 |
| --- | --- | --- | --- |
| 11-05 | #1 | `.gitignore` 加入 `UI_Agent_Work_Spec.md`；Day 1：`docs/ui-backlog.md`（UI User Stories、頁面清單）、`docs/ui-backend-contract.md`（契約草稿）；Day 2：根目錄 `app.py` 骨架、`templates/`（base、navbar、menu、cart、checkout、merchant、orders）、`static/css/style.css`、`requirements.txt`、建立 `.venv`；`docs/ui-project-summary.txt` | `71e47d3` 建立 Flask UI 頁面骨架 |
| 11-07 | #2 | 兩份 API schema（後補必填 `merchant_id`）；多商家契約改版；UI：購物車右下角總額預覽＋結帳按鈕、checkout 改為「付款頁」、orders 改用 `order.order_id`、移除導覽列付款入口 | `134e5e9` 更新多商家購物車 UI 契約 |
| 11-09 | #3、#4 | 無程式修改；釐清 root `app.py` 只是合併留下的骨架、`run.py` → `backend.app` 才是後端入口、當時訂單／付款 API 仍 501 | — |
| 11-09 | #5 | `templates/partials/order_summary.html`（購物車／結帳共用摘要）；重寫 `menu.html`（描述、商家標籤、數量驗證）、`cart.html`（數量調整／移除、即時小計）、`checkout.html`（唯讀摘要、冪等鍵、多訂單付款狀態）；新增 `static/js/cart.js`；`docs/backend-integration-requirements.md` | `065ad7b` Add SSR ordering UI integration contract |
| 11-10 | #7 | 本機 `instance/campus_ordering.db` 為舊版 schema 導致頁面 500 → 執行 `migrate-db` + `seed` 修復，`/health`、`/menu`、`/cart`、`/checkout`、`/merchant/*` 全部 200；關閉多個殘留 `python app.py` 程序釋放 port 5000 | （後端組的 `9fd75c6` 整合前端介面與後端訂購流程，經 `e7ac4c6`／`d32e6e7` 合併形成目前 `main`） |
| 11-10 | #8 | `docs/user-stories.md`（US-01～US-14 已實作＋US-B1～US-B8 backlog，含 Git 歷程對應）；`docs/uml/`：use_case、class_diagram、sequence_diagram（.puml / .svg / .png）＋README；`docs/architecture.md` 曾產出但目前已不存在於工作區 | **皆未 commit** |
| 11-11 | #9 | 僅完成看板規劃（讀 `user-stories.md`、規劃 22 張卡片與欄位），未執行 | — |

## 三、目前未完成 / 待解問題


1. **`docs/architecture.md` 消失**：`docs/user-stories.md` 第 11 節仍引用它，需重新生成或移除引用。
2. **功能 backlog**（出自 `docs/user-stories.md`）：
   - US-B1 商家切換（UI）（後端路由已存在、缺前端控制）
   - US-B2 正式登入與權限
   - US-B3 商品編輯／下架／庫存
   - US-B4 CSRF 防護
   - US-B5 真實金流
   - US-B6 JSON API
   - US-B7 前端商家切換控制
   - US-B8 商品圖片上傳
