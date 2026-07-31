<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=694741f

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：83（accepted 77、superseded 6）
- BACKLOG 待辦：36（next：B-127）｜滯後：2
- LESSONS：199 筆（next：L-200）
- events：34 筆（feature_close 19、misc 12、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-31｜misc｜B-123＋B-119 收單（維護輕量軌走 workflow 編排：maint-b123-b119 分支、implementer 與雙審皆 Fable xhigh、首輪雙審零 blocker）——preflight 補權限面三斷言（目錄 700／檔 644／owner 非 root、ERROR exit 1、置於 CR 與 composite 之前、drvfs v9fs 必紅指路 ADR 0080 ext4 拍板）＋佔位字面清單 WARN 不阻擋（PLACEHOLDER_LITERALS 逐字取自 generate-secrets.sh、位元組比對不印內容、命中指路 §7＋§15.4；升級成阻擋屬拍板級明文未做）；沙箱六案機證＋真落點唯讀 rc=0 全綠；RUNBOOK §15.4 口徑同步；merge SHA＝139ec9328699f9089490463efcd4cc3738dc6539
- 2026-07-31｜misc｜B-116 收單（維護輕量軌走 workflow 編排：maint-b116 分支、implementer 繼承 Fable×spec/quality 雙審 Opus xhigh、spec blocker 升級主線後 resumeFromRunId 續跑）——docs-sync 新增 L21 條款：EXEC_BIT_ROSTER 顯式名冊 14 支（hooks 4＋deploy 5＋python 工具 5、成員資格逐檔叫用形實證、被 source／恆 bash·sh 前綴者 6 支除外記註解）斷言 index stage-0 必 100755、缺席與空名冊 fail-closed ERROR、無 skip、每跑紅綠 self-test；測試 349→360、突變 A~D 全殺、fixture 零汙染真 index；RUNBOOK §12 補列＋範圍字串 L3~L21 同步（.githooks/pre-commit 檔頭漏改由主線 fbf65ee 結清、errata 0 殘留）；復發模式（連兩刀漏改範圍字串）登記 B-126；merge SHA＝25883752c1395d911f616f5670dd48ead6e2f211
- 2026-07-31｜misc｜B-117 收單（維護輕量軌首例走 workflow 編排：maint-b117 分支、implementer 繼承 Fable×spec/quality 雙審 Opus xhigh、六件套全套）——RUNBOOK §15.7 步驟 3 重加密改先寫同目錄 .new 再 mv 蓋回（[ -s ] 擋 rc=0 空檔、失敗清殘檔原檔不動、同裝置警語、與 §15.2 防法同構、< /dev/null 與 --filename-override 語意保留）；spec 審 stub 五案機證修前窗口存在／修後關閉、零 blocker；quality 審唯一 blocker（BACKLOG 未刪列）屬 fix agent 允許清單外、依空間邊界紀律升級主線刪列；merge SHA＝c4326e07dd0463b81b8ed75d0724c5adc4e4d911

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
