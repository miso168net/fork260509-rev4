<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=0e06e3e

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：75（accepted 70、superseded 5）
- BACKLOG 待辦：37（next：B-107）｜滯後：2
- LESSONS：151 筆（next：L-152）
- events：24 筆（feature_close 15、misc 8、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-19｜misc｜B-086 收單（user 拍板 2026-07-19 甲案：停用選單歸檔授權可復原）——restore 第⑥步 menu 存在判準換源 list_active→list_governed（治理域＝未刪含停用、對齊 010 FR-019 停用≠撤銷；軟刪 orphan 照舊 NotRestorable）；不一致實錘＝授權樹讀端已走治理域可對停用選單新授、唯復原被顯示域擋。Workflow 單元 wf_b9edde7d（implementer TDD＋spec/quality 雙審、3 agents 首輪零 blocker）；紅測 restore_menu_disabled_target_applies_governed 先紅後綠＋守恆補測軟刪案、容器內 --lib 694/0（基線 692＋2）；主線親驗硬錨（git 6c8ee72＋模組 20/0 親跑）；rust-api pin 531b412→6c8ee72；無 ADR（對齊既定 FR-019 語義之修正、比照維護批先例）；另錄 L-151（cd/pwd 生成慣性事故）
- 2026-07-19｜misc｜B-085 收單（user 拍板提前立案）——ADR 0068 accepted：校正 ADR 0050 字面漂移、protectedRevoke 拒因 key 正典＝biz.role.protectedRevoke（as-built 三處一致：rust handler／契約表／三語 locale；憲章路徑＝實作推翻拍板立新 ADR、0050 body 不動）；實作零改動、純文檔治理
- 2026-07-19｜misc｜B-106 收單（user 拍板調規 2026-07-19）——L9 反回收 HEAD 豁免視野改寬鬆子串形 RE_ENTRY_ANYPOS（｜為欄位分隔、散文引用不帶故字串曾現即非回收；staged 側計數/撞號維持嚴格行錨）；BACKLOG.md B-081 行尾黏連處補換行、B-083 復形獨立條目（B-106 刪列−1＋B-083 復形+1、STATE 待辦持平 39）；grep 實證全語料行中 B-NNN｜子串唯一例外即黏連本體、誤豁免面零；真回收（號碼已刪列＝HEAD 無字串）照抓、既有測試鎖住

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
