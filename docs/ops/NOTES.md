# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切）已收刀（005 merge 540bae1；pins/summary 見 events／STATE）：
  005 補齊授權 seam 另一半——jwt sign 升 prod＋TTL＋三態 router（Public/Authed/Policy）＋login（防枚舉
  collapse 1000＋dummy-argon2 時序拉平＋sys_login_attempt exactly-one）＋無狀態 sliding refresh（8888、
  sys_token 零寫）＋dynamic route 三端點（casbin menu 過濾＋祖先包含）＋4 alt-login stub（2222）；base-web
  dynamic 切換＋常數路由合併修＋stub 接线＋backend.auth.* i18n；gate2 additive 白名單（ADR 0032）；CDP 實機 9 項全驗。
- 下一步：波 1 續 **session 刀**（brainstorm 起手、建議新 session 給完整 runway）——B-021 一次設計完整
  （rotation／single-session／denylist／即時硬撤；rev3 三度改向），併 B-029（改密撤 session）／B-048（Redis 基建
  起手）／B-062（閒置 toast、需攔截器軌道 amendment）；005 已埋 seam（sys_token 表零寫、Claims.sid/jti、redis 設定、
  7777、ADR 0030 明示不預佔）、憲法 §I.7 行為島待入憲。auth family 建議次序（2026-07-06 拍板 next＝session）：
  session →（複用 Redis）節流刀（B-010 帳號級先落地）→（ingress 拓樸定案後）IP 閘刀（B-019/B-024，把節流升 IP 級）；
  理由＝session 續 005 seam 最緊、關「refresh 被竊無限續命／停用帳號殘留」缺口，IP 閘 ingress 拓樸前置不 front-load。
  005 遺留：B-060 demo 選單清理／B-061 3 manage 子項 i18n（各子系統刀補譯）。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器）。
