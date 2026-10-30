# 溪中魔『數』領域網站

桃園市立大溪國民中學數學領域網站，自 Weebly 搬移至 GitHub Pages。

網站：https://coolokey.github.io/dsjh-math/

原網站：https://dsjhmath.weebly.com/

## 保留範圍

- 保留原有 36 個導覽項目的名稱、順序及分類階層，其中 27 個標準頁面、9 個外部連結項目。
- 保留可讀取的原站內容、主題、圖片、教材與附件。
- 舊輪播轉成本機相簿，縮圖供瀏覽，點擊開啟備份原圖。
- 嵌入行事曆 PDF 改成本機文件，另提供直接開啟與下載連結。
- 確認為 HTTP 404／410 的外部連結取消超連結，保留原文；拒絕存取與網路逾時不視為已確認失效。
- 原 Weebly 留言服務停用，保留歷史欄位文字；未新增接收留言的後端。
- 原站搜尋依賴 Weebly 服務，未保留搜尋欄位；使用原有分類與站內連結瀏覽。

## 維護與發布

管理入口：https://coolokey.github.io/dsjh-math/admin/

操作指南：https://coolokey.github.io/dsjh-math/admin/guide.html

後臺採 Decap CMS 與單人 Turbo 免費方案；首次必須由擁有者完成帳號、GitHub App 授權及 Site ID 設定。尚未配置時入口會顯示未啟用，不能儲存或發布。詳見 `docs/cms-setup.md`。

`content/home.json` 與 `content/pages/*.json` 是正式內容來源，`body` 保留原 HTML，`blocks` 管理新增文字、文件、圖片、相簿及影片，首頁 `news` 管理新公告。原分類與既有頁面 ID 保留；改標題不改網址。`content/aliases.json` 保留舊網址導向。

執行 `python -m pip install -r requirements.txt` 後，使用 `python scripts/build.py` 驗證內容並重新產生 `site/`。不需本機 `backup/`。`scripts/layout.py` 與 `templates/base.html` 提供共用版型，`site/design.css` 與 `site/design.js` 提供前臺樣式和互動。

GitHub Actions 的 Publish math website 工作流程在 `main` 更新後驗證、建置與發布。PR 只驗證，不部署。CMS 儲存草稿與發布使用其編輯流程；正式網站在 Actions 部署成功後更新。取代之前人工 subtree 發布流程，`gh-pages` 保留作切換前的復原版本。

日常測試：

```powershell
python -m unittest discover -s tests -p test_content.py -v
python -m unittest discover -s tests -p test_cms_release.py -v
node --test tests/editor.test.cjs tests/bootstrap.test.cjs
```

`tests/test_redesign.py` 比對搬站原文、附件和照片順序，僅供首次轉換完整性驗收。使用者日後正式修改／刪除內容後，不再要求原文永久不變。`scripts/verify.py` 與 `scripts/migrate_legacy.py` 保留舊搬站稽核用途，仍需 ignored `backup/`，不屬日常建置。

`docs/` 保存搬移、改版、後臺設定與驗證紀錄。外部相簿和影片維持外部服務連結，其後續可用性取決於原服務。
