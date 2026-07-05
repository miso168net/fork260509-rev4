# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1 首功能刀 004-system-settings 已收刀（merge cf20d29；pins/summary 見 events／STATE）：
  dev stack＋基線 schema/seed＋wire 信封/13 碼/契約管線（波 0）；授權 seam（enforce_mw+require_policy
  super-only casbin、DB-fresh roles）＋facade/op-log（同 txn、KV String-PK）＋型別驗證 registry（ADR 0026）
  ＋系統設定兩端點＋base-web 首刀（US1 頁＋全 zh-TW primary locale 525 鍵＋三語選單）＋entity_access_lint
  ＋per-route 契約裁判＋demo 清償（活書 §5／§8）。
- 下一步：波 1 續下一功能刀（brainstorm 起手）——auth 刀承 004 的 enforce_mw／require_policy seam、接續
  JWT sign／登入端點（消化 B-008）；base-web login-gated live 走查亦留 auth 刀（004 拍板 7）；user-center 等隨排。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器）。
