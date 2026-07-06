# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切、006 會話生命週期）已收刀（006 merge 209d9a0；
  pins/summary/ADR 見 events／STATE）：006 DB-stateful 化 supersede ADR 0030——refresh rotation（FOR UPDATE
  lock-then-redecide L-075）＋reuse 偵測撤 family＋grace 冪等（並發不誤撤）＋single-session 踢除（advisory
  lock＋7777）＋即時撤銷（denylist Redis 快取＋PG 權威 fail-closed）＋伺服器登出（/auth/logout）＋精確 idle
  （last_activity 熱快取、僅 valid-access 推進）＋Redis 起手（ConnectionManager 1.3.0）＋最小會話稽核
  （session_event 變體B）；憲法 v1.3.0（§I.7 島 A/B/C/D＋LOGOUT-UX-WIRING）；ADR 0033(DB-stateful)/0034(軌道)/
  0035(T034 won't-fix)/0036(alova toast won't-fix)；cargo test 148 綠、CDP-1~4 實機全綠（CDP 揪出補 7777 modal
  i18n＝L-053/L-015 兌現）。★006 分支未 push（user 定 push 時機 (b)）。
- 下一步：波 1 續 **節流刀**（B-010 帳號級先落地、複用 006 Redis 基建）——登入失敗節流以合成終態重設計
  （一般化訊息＋鎖中不逐筆稽核已反轉原案）；併 B-017（fail-OPEN 範圍重估＋降級告警）／B-018（惡意鎖人 DoS 面）／
  B-032/B-033（強化包／快取遞延組）。auth family 次序（2026-07-06 拍板）：session（done）→節流刀（B-010）→
  （ingress 拓樸定案後）IP 閘刀（B-019/B-024 升 IP 級）；理由＝節流複用 006 Redis 最緊、IP 閘 ingress 前置不 front-load。
- 006 遺留 primitive／再議：停用帳號/改密/admin 踢除端點（B-064、消費 revoke_others_of_user primitive＋發
  session_event(revoked)；併 B-029 改密撤 session）；alova 棧接入真實 auth 時補 idle toast＋onError i18n
  （B-069、ADR 0035/0036 觸發再議）；孤兒 reaper（B-063）／並發登入收斂整合測試（B-066）。005 遺留 B-060/B-061 仍在。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器＋CDP 實機）。
- ★新 i18n key 加入後 CDP 前需 restart base-web（vite dev 未必熱載新字典、否則 toast/modal 顯 raw key、L-015）。
