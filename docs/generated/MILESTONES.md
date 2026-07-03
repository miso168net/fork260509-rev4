<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# MILESTONES — 全事件表（2026）

| date | type | 標的 | summary | merge | adrs | arch |
|---|---|---|---|---|---|---|
| 2026-07-03 | misc | — | rev4 bootstrap（波 -1 文件地基）完成：B1~B9 全落地、DoD 驗收全綠、啟動書退役轉存 brainstorms/000-doc-architecture | — | — | — |
| 2026-07-03 | feature_close | 001-compose-stack | 一鍵開發環境落地：compose 兩件套（六 service＋migrate gate）＋六機密 _FILE 機制＋自簽 TLS＋rust-api scaffold（axum /health＋migration 空殼）＋雙端輪詢熱重載＋ports extractor（B-002 落地）；quickstart A~H 全綠、與 rev3 同機並行實測零衝突、base-web 零 fork 改動 | a35f2736b51be7a368bafc7da3aee6dfd06e1082 | 0022 | §2、§7 |
