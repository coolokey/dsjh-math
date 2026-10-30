# Single-owner CMS Implementation Plan

> 執行方式：使用 subagent-driven-development，依獨立責任分工，保留任務與整體複核。

**Goal:** 提供單人內容管理、草稿及自動發布，保留既有網站。

**Architecture:** content/home.json、content/pages/*.json 為正式來源，body 保留既有 HTML；blocks 提供新文字、圖片、文件、相簿。Decap CMS 自訂保留 HTML 的編輯器；Turbo 免費單人登入；Actions 從 main 建置及部署。

**Tech Stack:** Python、BeautifulSoup、Markdown、Decap CMS 3.17.1、GitHub Actions。

## 合約

頁面 JSON：id、title、parent（空字串或父 ID）、order（整數）、hidden、external、body（HTML）、blocks（陣列）。home 位於 content/home.json，ID 固定 394608272104688055，另含 hero_image。其他頁面為 content/pages/{id}.json。新增 ID 由自訂唯讀 widget 產生，URL 為 page-{id}.html。blocks type 為 text（text Markdown）、image（file、caption）、document（file、caption）、gallery（images：file、caption）、video（url）。content/aliases.json 保存既有別名。所有資源為 assets/... 或 /dsjh-math/assets/...。

## Task 1：正式內容與建置

- [x] 先建立失敗測試：不含 backup 仍能建置、新增與隱藏／刪除頁面、循環／缺父／重複 ID、危險 HTML／本機附件失效會攔截。
- [x] 從目前 site HTML 擷取內容並保存全部 36 頁、既有首頁圖與別名；保持所有文字及相簿順序。
- [x] 以 scripts/content.py 載入及驗證資料，scripts/build.py 改為正式內容建置；舊搬站程式保留 scripts/migrate_legacy.py 供封存。
- [x] layout.py 支援已整理內容、固定首頁 ID、hidden 導覽與穩定 URL；不用 backup 也能建置。
- [x] 執行 unittest，保留原基準測試；針對新增、修改、隱藏、刪除、還原及 blocks 做 tempdir 驗證，避免測試資料公開。

## Task 2：編輯介面

- [x] site/admin/editor.js 註冊 HTML 編輯 widget 與固定 ID widget；iframe sandbox 隔離、保留原結構、文字工具列、HTML 進階模式、內容預覽。
- [x] 未編輯往返不得改原內容；既有相簿／PDF 不因文字修改遺失；資源路徑依前臺 base URL 解析。
- [x] site/admin/config.yml 使用 JSON collections、首頁獨立不可刪除、其他頁面可新增與刪除、parent relation、排序、hidden 與 blocks 欄位。
- [x] 編輯器禁止 script、事件屬性、javascript URL，建置端同步強制驗證。以語法與瀏覽器操作驗證，不以模擬登入宣稱真實發布。

## Task 3：登入、發布及文件

- [x] admin/index.html 提供正式 CMS 與未設定 Turbo 時的清楚設定狀態；不提供公開可寫的測試 backend。
- [x] config.yml 暫存可讀的未啟用設定標示，取得實際 site UUID 後才啟用；不寫假的帳號／金鑰。
- [x] .github/workflows/pages.yml：push main、PR 驗證、手動執行，安裝鎖定 Python 依賴，建置、內容驗證；成功才部署 site/。PR 不公開部署。最小權限，部署限 main。
- [x] 中文操作指南涵蓋註冊授權、config path、草稿公開性、上傳／編輯／發布／還原及 Actions 狀態。
- [ ] 整體複核與本機畫面 QA 後推送 main，切換 Pages source 至 workflow，等待部署並驗證正式網頁及 admin；帳號授權交由使用者親自完成，後續實測登入及儲存發布才能稱完成。

## Rulings

- 使用者已批准實作及既有網站發布，例行程式推送不重複詢問。
- 服務條款與新增 GitHub App 權限由本人操作；在此之前完成所有獨立開發、測試與可檢視設定，不把公開入口視為可用後臺。

## 驗證進度

- 正式內容、編輯器與自動發布程式已實作；Python 12 項、Node 8 項測試通過。
- CUA 已驗證實際 Decap UI 使用本機 test-repo 編輯及儲存保留表格、相片、PDF；正式 config 欄位載入成功。僅本機測試，沒有真實帳號發布。
- 獨立複核發現的預覽不更新已修正並新增測試；現無待修程式問題。
- 後續：正式部署與線上檢查；本人帳號註冊／授權與實際發布驗收。

- Ruling：線上 HTML 比對發現 Windows CRLF 與 Linux LF 導致樣式版本碼不同；統一雜湊換行並新增 portability 測試，保留真實位元組比對標準。

- 正式部署 17a6f8c，Actions 40992120791 成功，線上 100 項位元組檢查全部通過；正式管理入口與指南、原首頁圖均經 CUA 驗證。本人註冊／授權及真實帳號發布驗收仍待完成。
