# 分工與工作流程

- A（PO／學生端）：先改 `frontend/templates/student/`，依 GET products 實作畫面；等待 C 的 orders API；審核 Stories 並畫 Use Case。
- B（Scrum Master／商家端）：先改 `frontend/templates/merchant/`，串 GET/POST products；人工建立 Issues／看板與真實紀錄；等待 orders API 並畫 Activity。
- C（後端／整合）：擁有 `backend/`、`run.py`、schema 與 API；下一步實作 US05/US06/US07、Class UML 與測試。

`main` 只放已審核版本；建議分支 `feature/student-ui`、`feature/merchant-ui`、`feature/backend`。完成後開 PR 且至少一人 Review。共用檔變更先溝通；不可捏造 commit、核准或會議證據。
