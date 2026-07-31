<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=694741f

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：83（accepted 77、superseded 6）
- BACKLOG 待辦：34（next：B-127）｜滯後：2
- LESSONS：199 筆（next：L-200）
- events：37 筆（feature_close 19、misc 15、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-31｜misc｜B-114 收單（維護輕量軌走 workflow 編排：maint-b114 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——index_pins 逐庫復用 index_gitlink 歸一 018 嚴格 stage-0 語意（回傳形 (SHA, 跳過原因) 同契約、零第二份過濾邏輯）；gitlink 衝突態與缺席 STATE 顯「未定（原因）」絕不顯 stage 值；條目誤述據實勘正（舊碼末筆 stage 3 theirs 勝出、非「首筆＝祖先」，tempdir 探針實證）；測試 360→364、突變殺證、真 repo generate 零 diff 健康態零回歸、L17/L18 零轉紅；merge SHA＝11efe94bbeafd64b02b52d962a1ace864f232586
- 2026-07-31｜misc｜B-124 收單（維護輕量軌走 workflow 編排：maint-b124 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——bootstrap S5 補 hooks 標的檔內容指紋斷言：git hash-object（走 filter、CRLF 不假紅有實證）對 HEAD blob 逐檔比對 .githooks-submodule/pre-commit 與 pre-push、缺檔／不在 HEAD／內容不符三分支 die 指名、內容不符含雙情境指引（疑遭 simple-git-hooks 覆寫 vs 本人未 commit）；閉合「覆寫標的檔、hooksPath 指標值不變仍印 ok」靜默失效窗口；受控突變機證三段＋缺檔分支加測、幂等純唯讀；RUNBOOK §12 補償句同步；merge SHA＝7d6f773898f159cefbea7716ba890f45824f991b
- 2026-07-31｜misc｜B-118 收單（維護輕量軌走 workflow 編排：maint-b118 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——secret-value-guard 加 check --full-tree 一次性全樹盤點模式（讀落點現值×掃全 tracked blob、只印檔案:行號｜機密名絕不印值、gitlink 160000 濾除、binary 跳過、自帶紅綠 self-test；staged 預設模式零回歸＝前後 stdout/stderr/rc 逐 byte 相同）；測試 41→51、突變殺證；真 repo 體檢零命中（445 支 tracked 檔、約 1.6~1.8 秒、耗時記 RUNBOOK §12 供未來 pre-commit 接入拍板、本單元明文不接）；B-118 盲區對 pre-commit 閘仍為真、本模式屬補償性盤點工具；merge SHA＝e5a15c3b23e50b7e97f8b7cc88ee040202971061

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
