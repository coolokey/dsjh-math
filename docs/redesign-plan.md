# Academic Editorial Redesign Implementation Plan

> 執行方式：依已確認的 `docs/redesign-proposal.md` 在本次工作中完成，保留檢查與實際畫面驗證作為階段檢核。

**Goal:** 完成現代學園刊物版面，保留內容、分類、網址與素材並發布。

**Architecture:** 沿用 `scripts/build.py` 的資料還原流程，新增 `scripts/layout.py` 將清理後內容套用語意化共用版型。`site/design.css` 與 `site/design.js` 負責視覺及導覽、文件與相片互動；不新增伺服器。

**Tech Stack:** Python、BeautifulSoup、靜態 HTML、CSS、JavaScript、GitHub Pages。

## 1．建立保留基準與需求檢查

- [x] 將既有 27 頁的 `#main-wrap` 文字節點、相片連結及文件路徑保存為 `backup/redesign-baseline.json`。
- [x] 新增 `tests/test_redesign.py`，檢查新頁首／主內容、目前頁面標示、可展開 PDF、全部內容與素材保留。
- [x] 執行 `python -m unittest discover -s tests -v`，確認新版面需求尚未實作而失敗。

## 2．共用版型與內容呈現

- [x] 新增 `scripts/layout.py`，輸出共用頁首、完整分類、麵包屑、頁名、側欄及頁尾；`scripts/build.py` 改呼叫新產生器。
- [x] 首頁沿用原兩欄內容，將近期公告與可展開歷史公告分開；保留所有原文及原更新日期。
- [x] 保留文件直接連結，將嵌入 PDF 放入預設收合的預覽區，展開後才載入。
- [x] `site/design.css` 統一暖白／墨綠視覺、閱讀字級、文章、表格、影片與相簿；手機保留足夠觸控區及閱讀寬度。
- [x] `site/design.js` 實作手機導覽、分類展開、按需文件預覽、原圖前後切換、鍵盤與焦點還原。
- [x] 執行 `python scripts/build.py`、`python -m unittest discover -s tests -v` 與 `python scripts/verify.py`，全部通過。

## 3．畫面、完整性與發布

- [x] 啟動本機預覽，檢查首頁、文件、獲獎表格、相簿及影片在桌機與手機的實際畫面。
- [x] 實測手機導覽、分類切換、PDF 展開、原圖前後切換與 Escape 關閉。
- [x] 獨立複核新共用版型、內容保留與互動，修正必要問題。
- [x] 合併至 `main`，推送原儲存庫並以 `git subtree push --prefix site origin gh-pages` 發布。
- [x] 等待 GitHub Pages 部署成功，執行 `python scripts/verify_live.py`，再檢查正式網站的桌機與手機畫面。
