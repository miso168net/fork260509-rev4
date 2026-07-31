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
- events：36 筆（feature_close 19、misc 14、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-31｜misc｜B-124 收單（維護輕量軌走 workflow 編排：maint-b124 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——bootstrap S5 補 hooks 標的檔內容指紋斷言：git hash-object（走 filter、CRLF 不假紅有實證）對 HEAD blob 逐檔比對 .githooks-submodule/pre-commit 與 pre-push、缺檔／不在 HEAD／內容不符三分支 die 指名、內容不符含雙情境指引（疑遭 simple-git-hooks 覆寫 vs 本人未 commit）；閉合「覆寫標的檔、hooksPath 指標值不變仍印 ok」靜默失效窗口；受控突變機證三段＋缺檔分支加測、幂等純唯讀；RUNBOOK §12 補償句同步；merge SHA＝7d6f773898f159cefbea7716ba890f45824f991b
- 2026-07-31｜misc｜B-118 收單（維護輕量軌走 workflow 編排：maint-b118 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——secret-value-guard 加 check --full-tree 一次性全樹盤點模式（讀落點現值×掃全 tracked blob、只印檔案:行號｜機密名絕不印值、gitlink 160000 濾除、binary 跳過、自帶紅綠 self-test；staged 預設模式零回歸＝前後 stdout/stderr/rc 逐 byte 相同）；測試 41→51、突變殺證；真 repo 體檢零命中（445 支 tracked 檔、約 1.6~1.8 秒、耗時記 RUNBOOK §12 供未來 pre-commit 接入拍板、本單元明文不接）；B-118 盲區對 pre-commit 閘仍為真、本模式屬補償性盤點工具；merge SHA＝e5a15c3b23e50b7e97f8b7cc88ee040202971061
- 2026-07-31｜misc｜B-123＋B-119 收單（維護輕量軌走 workflow 編排：maint-b123-b119 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——preflight 補權限面三斷言（目錄 700／檔 644／owner 非 root、ERROR exit 1、置於 CR 與 composite 之前、drvfs v9fs 必紅指路 ADR 0080 ext4 拍板）＋佔位字面清單 WARN 不阻擋（PLACEHOLDER_LITERALS 逐字取自 generate-secrets.sh、位元組比對不印內容、命中指路 §7＋§15.4；升級成阻擋屬拍板級明文未做）；沙箱六案機證＋真落點唯讀 rc=0 全綠；RUNBOOK §15.4 口徑同步；merge SHA＝139ec9328699f9089490463efcd4cc3738dc6539

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
