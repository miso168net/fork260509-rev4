<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=531b412

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：68（accepted 63、superseded 5）
- BACKLOG 待辦：38（next：B-107）｜滯後：2
- LESSONS：150 筆（next：L-151）
- events：23 筆（feature_close 15、misc 7、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-19｜misc｜B-085 收單（user 拍板提前立案）——ADR 0068 accepted：校正 ADR 0050 字面漂移、protectedRevoke 拒因 key 正典＝biz.role.protectedRevoke（as-built 三處一致：rust handler／契約表／三語 locale；憲章路徑＝實作推翻拍板立新 ADR、0050 body 不動）；實作零改動、純文檔治理
- 2026-07-19｜misc｜B-106 收單（user 拍板調規 2026-07-19）——L9 反回收 HEAD 豁免視野改寬鬆子串形 RE_ENTRY_ANYPOS（｜為欄位分隔、散文引用不帶故字串曾現即非回收；staged 側計數/撞號維持嚴格行錨）；BACKLOG.md B-081 行尾黏連處補換行、B-083 復形獨立條目（B-106 刪列−1＋B-083 復形+1、STATE 待辦持平 39）；grep 實證全語料行中 B-NNN｜子串唯一例外即黏連本體、誤豁免面零；真回收（號碼已刪列＝HEAD 無字串）照抓、既有測試鎖住
- 2026-07-19｜misc｜BACKLOG 滯後卷機制建立（docs/ops/BACKLOG-DEFERRED.md、user 拍板 2026-07-19）——docs-sync 多卷化：open_ids／L9／L4／L5／ever-existed 全卷同視野（滯後≠完成、條目仍屬開放）＋STATE 待辦/滯後分計＋L14 錨禁擴卷＋預算表納卷；B-060、B-103 整行移入滯後卷（正式 release 前清理批；B-060 屆時仍先重偵察＋順路 B-101/B-094）；NOTES 下一步改 auth 組 vs prod 組擇定；施工偵察發現 B-081 行尾黏連 B-083 致其隱形於計數與 lint 視野、立案 B-106（修復需 lint 調規拍板）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
