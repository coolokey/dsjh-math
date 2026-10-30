# 單人管理後臺：啟用與維護

管理入口：https://coolokey.github.io/dsjh-math/admin/

公開操作指南：site/admin/guide.html。選用 Decap CMS 3.17.1、Turbo Free（一個網站、一人）。目前未設定真實 Turbo Site ID 時，入口明確顯示未啟用，不載入 CMS 或任何測試寫入後端。

## 由本人完成的設定

1. 在 https://turbo.decapcms.org/ 註冊，閱讀及接受服務條款，選 Free，不建立付費訂閱。
2. 在官方流程連接 GitHub App，只授權 coolokey/dsjh-math，由本人確認實際權限。保持一位成員。
3. 建站資料：repo=coolokey/dsjh-math，branch=main，admin URL=https://coolokey.github.io/dsjh-math/admin/，config path=site/admin/config.yml。
4. 複製 Overview 的 Site ID（公開 UUID），填入 site/admin/config.yml 的 backend.turbo_site_id；不需提供密碼、OTP、OAuth secret 或個人 token。
5. 提交 main 後，等待 Publish math website 工作流程成功，正式入口才會顯示 Turbo 登入。

## 必須親測的帳號驗收

登入成功不等於完成：需由實際帳號新增測試頁、儲存草稿、發布、正式網址讀取、修改、上傳教材與圖片、隱藏、刪除、還原，並確認未登入不能寫入。測試後清理測試內容，保留實際 Actions 執行與畫面證據。未完成帳號授權前，報告應標示「程式與部署已驗證，帳號串接及實際編輯發布待驗」。

## 建置與版本

正式來源 content/，既有 HTML 留存在 body，不依賴 backup/。scripts/migrate_legacy.py 僅封存搬站流程，不能作為日常更新指令。新 build.py 驗證資料後產生 site/。GitHub Actions 在 main 提交後建置與部署；PR 僅驗證，不部署。

第一次切換 Pages source 前，保存原 gh-pages commit；若需回復，將 Pages source 設回 gh-pages 根目錄即可先回到舊發布。網站內容的誤改應以 git revert 還原修改，再由 Actions 重新部署。

tests/test_redesign.py 與 tests/baseline.json 是搬移完整性基準，只適用於首次轉換驗收；日後使用者正式刪除或改寫內容後，不應再要求所有歷史文字不變。日常 CI 使用獨立內容模型與發布邊界測試，並由 build.py 檢查目前實際內容。

## 參考

- https://decapcms.org/docs/turbo-connecting-a-site/
- https://decapcms.org/docs/editorial-workflows/
- https://decapcms.org/docs/custom-widgets/
