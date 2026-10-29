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

新版採現代學園刊物版面，保留原分類與素材。`scripts/layout.py` 與 `templates/base.html` 產生共用結構，`site/design.css`、`site/design.js` 提供版面與互動；CSS／JS 參照包含內容雜湊版本，避免沿用舊快取。

執行 `python -m unittest discover -s tests -v` 可比對改版前原文、文件連結、照片順序、分類及按需 PDF 預覽。原有素材完整性檢查維持不變。

`site/` 是實際發布內容。原始碼保存在 `main`，以 `git subtree push --prefix site origin gh-pages` 將網站目錄發布到 `gh-pages` 分支；GitHub Pages 從該分支根目錄建置與部署。

`scripts/` 保存素材下載、連結檢查、頁面轉換與完整性驗證程式。Python 需要 requests、beautifulsoup4、Pillow。

本機原始擷取檔位於 `backup/`，已從 Git 排除；不發布登入狀態或後台預覽內容。執行 `python scripts/build.py` 重新產生頁面，再執行 `python scripts/verify.py` 檢查。

`docs/` 保存搬移計畫、略過連結與驗證結果。外部相簿和影片維持外部服務連結，其後續可用性取決於原服務。
