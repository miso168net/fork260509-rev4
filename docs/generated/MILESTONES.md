<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# MILESTONES — 全事件表（2026）

| date | type | 標的 | summary | merge | adrs | arch |
|---|---|---|---|---|---|---|
| 2026-07-03 | misc | — | rev4 bootstrap（波 -1 文件地基）完成：B1~B9 全落地、DoD 驗收全綠、啟動書退役轉存 brainstorms/000-doc-architecture | — | — | — |
| 2026-07-03 | feature_close | 001-compose-stack | 一鍵開發環境落地：compose 兩件套（六 service＋migrate gate）＋六機密 _FILE 機制＋自簽 TLS＋rust-api scaffold（axum /health＋migration 空殼）＋雙端輪詢熱重載＋ports extractor（B-002 落地）；quickstart A~H 全綠、與 rev3 同機並行實測零衝突、base-web 零 fork 改動 | a35f2736b51be7a368bafc7da3aee6dfd06e1082 | 0022 | §2、§7 |
| 2026-07-04 | feature_close | 002-schema-baseline | 基線 schema＋seed 落地：m001 建表（11 業務表＋casbin 委派＋治理欄）＋m002 定稿 seed 244 列（argon2 執行期雜湊、冪等可逆、掛 001 migrate 閘門）＋tools/schema-gate 三閘（gate1 結構零漂移 vs 凍結 fixtures 含 --live-rev3 交叉、gate2 欄序/seed 定稿落實、audit 審計欄四變體守門＋archetype-map）＋entity crate 13 檔（欄序照定稿）＋docs-sync refresh 快照管線（reference/schema＋accounts 轉真＝B-003/B-004 落地）；quickstart A~G 全綠、SC-001~008 全過、001 SC-007 迴歸 18.86s、base-web 零 fork 改動、rev3 零擾動；閘 1 抓出定稿產物漏摺 2 索引並補齊（L-102） | ef5fe57a3b8311d252df3ba119560d97b251e929 | 0023、0024 | §5、§8 |
