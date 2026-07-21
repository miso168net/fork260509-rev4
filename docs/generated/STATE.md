<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=d4c66e0｜rust-api=e27290a

## constitution
- 版本：1.14.0

## 帳面統計
- ADR：75（accepted 70、superseded 5）
- BACKLOG 待辦：30（next：B-111）｜滯後：2
- LESSONS：154 筆（next：L-155）
- events：28 筆（feature_close 16、misc 9、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-07-21｜misc｜B-108 收單（RUNBOOK 驗證 WSL2 環境輪執行完畢、詳同日 review 事件與 docs/reviews/20260719-RUNBOOK-verify-wsl.md）——review 事件 schema 無 backlog_done 欄、依 2026-07-17 調規以 misc 輕量軌唯一證據通道記機器證據
- 2026-07-21｜review｜RUNBOOK 驗證 WSL2 環境輪（wf_9036ce9f-53a、動態對照串行×3＋報告簿記×1；mac 輪 E1／D1~D6 七項發現之 WSL2 對照全 pass＋覆蓋缺口三條補實〔§5 卷清時機／§9 unlockLogin ip 維／§11 告警投遞全鏈雙向閉環〕；13 項五態裁決：11 pass／1 adapted〔Super 單超管自鎖雞蛋相依、窗滿補證〕／0 doc_drift／1 skipped〔down -v、理由全文入報告〕／0 fail＋env 觀察 1 則〔冷編 41.99s vs mac 約 240s、警語或然語意照舊有效〕；零修零轉零 wont-fix；B-108 就此收單〔機器證據見同日 misc 事件〕；報告＝docs/reviews/20260719-RUNBOOK-verify-wsl.md〔檔名沿 user 指定與 mac 輪配對、實際執行日 2026-07-21〕）
- 2026-07-19｜review｜RUNBOOK 全 14 節命令實跑＋文件符實驗證（macOS 輪、wf_1d0bb1d5-154、12 agents 約 200 項裁決、零 fail：174 pass／14 adapted／6 doc_drift／6 skipped；doc_drift 6 全修同 commit 落地＋WSL2 環境輪轉 B-108）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
