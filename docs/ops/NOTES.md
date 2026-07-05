# NOTES — 當前意圖／下一步

- 波 0（001~003）＋波 1（004 系統設定、005 認證縱切）已收刀（005 merge 540bae1；pins/summary 見 events／STATE）：
  005 補齊授權 seam 另一半——jwt sign 升 prod＋TTL＋三態 router（Public/Authed/Policy）＋login（防枚舉
  collapse 1000＋dummy-argon2 時序拉平＋sys_login_attempt exactly-one）＋無狀態 sliding refresh（8888、
  sys_token 零寫）＋dynamic route 三端點（casbin menu 過濾＋祖先包含）＋4 alt-login stub（2222）；base-web
  dynamic 切換＋常數路由合併修＋stub 接线＋backend.auth.* i18n；gate2 additive 白名單（ADR 0032）；CDP 實機 9 項全驗。
- 下一步：波 1 續下一功能刀（brainstorm 起手）——user-center（B-057）／使用者管理（啟用 status UI、消化 005
  停用防禦 forward-compat）／session 刀（B-021 rotation/single-session/denylist）／節流刀（B-010）隨排。005 遺留
  BACKLOG：demo 選單清理（B-060）／3 manage 子項 i18n（B-061）／閒置過期輕量 toast（B-062、需攔截器軌道 amendment）。
- base-web 改動走 fork-delta 原行紀律（tools/fork-delta-lint 以 example 為基線機器強制、掛 pre-commit 於
  base-web pin 變動時擋）；base-web worktree commit 一律 `--no-verify`（host husky 不可用、驗證走容器）。
