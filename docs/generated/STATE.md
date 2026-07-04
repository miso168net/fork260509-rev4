<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=9c6f223｜rust-api=1809dd9

## constitution
- 版本：1.0.0

## 帳面統計
- ADR：24（accepted 23、superseded 1）
- BACKLOG 待辦：53（next：B-055）
- LESSONS：101 筆（next：L-102）
- events：2 筆（feature_close 1、misc 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-03｜feature_close｜001-compose-stack｜一鍵開發環境落地：compose 兩件套（六 service＋migrate gate）＋六機密 _FILE 機制＋自簽 TLS＋rust-api scaffold（axum /health＋migration 空殼）＋雙端輪詢熱重載＋ports extractor（B-002 落地）；quickstart A~H 全綠、與 rev3 同機並行實測零衝突、base-web 零 fork 改動
- 2026-07-03｜misc｜rev4 bootstrap（波 -1 文件地基）完成：B1~B9 全落地、DoD 驗收全綠、啟動書退役轉存 brainstorms/000-doc-architecture

## reference 對賬
- reference/routes：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
- reference/accounts：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
- reference/screens：stub（來源未就緒；extractor 隨對應子系統首刀落地，見 ops/BACKLOG）
