<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=9c6f223｜rust-api=0cad6b6

## constitution
- 版本：1.0.0

## 帳面統計
- ADR：25（accepted 24、superseded 1）
- BACKLOG 待辦：52（next：B-056）
- LESSONS：104 筆（next：L-105）
- events：3 筆（feature_close 2、misc 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-04｜feature_close｜002-schema-baseline｜基線 schema＋seed 落地：m001 建表（11 業務表＋casbin 委派＋治理欄）＋m002 定稿 seed 244 列（argon2 執行期雜湊、冪等可逆、掛 001 migrate 閘門）＋tools/schema-gate 三閘（gate1 結構零漂移 vs 凍結 fixtures 含 --live-rev3 交叉、gate2 欄序/seed 定稿落實、audit 審計欄四變體守門＋archetype-map）＋entity crate 13 檔（欄序照定稿）＋docs-sync refresh 快照管線（reference/schema＋accounts 轉真＝B-003/B-004 落地）；quickstart A~G 全綠、SC-001~008 全過、001 SC-007 迴歸 18.86s、base-web 零 fork 改動、rev3 零擾動；閘 1 抓出定稿產物漏摺 2 索引並補齊（L-102）
- 2026-07-03｜feature_close｜001-compose-stack｜一鍵開發環境落地：compose 兩件套（六 service＋migrate gate）＋六機密 _FILE 機制＋自簽 TLS＋rust-api scaffold（axum /health＋migration 空殼）＋雙端輪詢熱重載＋ports extractor（B-002 落地）；quickstart A~H 全綠、與 rev3 同機並行實測零衝突、base-web 零 fork 改動
- 2026-07-03｜misc｜rev4 bootstrap（波 -1 文件地基）完成：B1~B9 全落地、DoD 驗收全綠、啟動書退役轉存 brainstorms/000-doc-architecture

## reference 對賬
- reference/routes：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
