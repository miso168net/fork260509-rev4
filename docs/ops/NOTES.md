# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切、006 會話生命週期）已收刀（006 merge 209d9a0；
  pins/summary/ADR 見 events／STATE）：006 DB-stateful 化 supersede ADR 0030——refresh rotation（FOR UPDATE
  lock-then-redecide L-075）＋reuse 偵測撤 family＋grace 冪等（並發不誤撤）＋single-session 踢除（advisory
  lock＋7777）＋即時撤銷（denylist Redis 快取＋PG 權威 fail-closed）＋伺服器登出（/auth/logout）＋精確 idle
  （last_activity 熱快取、僅 valid-access 推進）＋Redis 起手（ConnectionManager 1.3.0）＋最小會話稽核
  （session_event 變體B）；憲法 v1.3.0（§I.7 島 A/B/C/D＋LOGOUT-UX-WIRING）；ADR 0033(DB-stateful)/0034(軌道)/
  0035(T034 won't-fix)/0036(alova toast won't-fix)；cargo test 148 綠、CDP-1~4 實機全綠（CDP 揪出補 7777 modal
  i18n＝L-053/L-015 兌現）。
- 下一步：**節流刀 brainstorm 已定案並經對抗式審查修訂**（`docs/brainstorms/007-login-throttle.md`、commit cb12bbf；
  11 題拍板、5 blocker＋23 major＋17 minor 全折入 §0.1）→ **由 user 手動起 `/speckit-specify`**（input＝該檔；
  絕不自動觸發、否則 spec 落 default branch）。設計要點：per-user 純帳號級（per-IP 待 IP 閘刀——rev3 019 是
  013 信任錨的下游消費者、防偽 IP 是前提，rev4 無等值基建）；L1 負快取僅由 L2 再判路徑寫入；稽核收斂為
  「只有 argon2 驗過的終局才落列」；CAPTCHA 軟區（無狀態 HMAC 簽題、產題零 Redis 寫入）；七源降級矩陣全鏈
  fail-OPEN（唯一例外＝unlock marker 讀失敗）；m005 settings 三鍵；nginx limit_req 納 scope。
  ★實作期先決：§9 四項測試機制（DbErr 注入 seam／tracing 捕捉層／raw SQL 種 created_at／自簽 challenge）
  必須先建，否則守門測試恆綠。產出規劃 ADR 0037-0040＋憲法 v1.4.0（島 E＋新軌道同筆 Amendment）。
  auth family 次序（2026-07-06 拍板）：session（done）→節流刀（B-010）→（ingress 拓樸定案後）IP 閘刀。
- 006 遺留 primitive／再議：停用帳號/改密/admin 踢除端點（B-064、消費 revoke_others_of_user primitive＋發
  session_event(revoked)；併 B-029 改密撤 session）；alova 棧接入真實 auth 時補 idle toast＋onError i18n
  （B-069、ADR 0035/0036 觸發再議）；孤兒 reaper（B-063）。005 遺留 B-060/B-061 仍在。
- 節流刀前清理批次已收（詳 git 2026-07-07~10：docs-sync L4/L5/L6＋reference 五表全轉真＋fork-delta 新增型
  圈界 lint＋wf-watchdog realpath＋B-068 session_event source_ip＋B-066 真並發測試）。節流刀直接輸入：
  ★B-066 harness（雙 committed 連線＋cleanup_user_artifacts＋pg_locks 等待輪詢，auth.rs mod tests「B-066」節）
  可複用於節流計數 race／審計恰一筆並發測試；★B-071 gate1 現紅（m004 結構新增無容差）——節流刀若帶
  migration 於 schema 期必拍（與 B-055 varchar 長度綁同一拍板批次、一次 ADR＋一次重擷取）。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器＋CDP 實機）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite dev 未必熱載新字典、否則 toast/modal 顯 raw key、L-015）。
