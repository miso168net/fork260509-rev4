---
id: "0034"
title: 新增 ★BASE-WEB-LOGOUT-UX-WIRING 軌道（logout server-call 接线＋閒置登出 toast 兩用途）
date: 2026-07-06
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-06 006-session-lifecycle brainstorm 拍板 6/7＋plan Constitution Check Q2/Q7（user 親決 2026-07-06）；需求源＝拍板7 /auth/logout 伺服器端撤銷＋B-062 閒置 toast"
tags: [constitution-amendment, fork-delta, base-web, auth, session]
---

## 背景

006 交付兩件需動 base-web inline，皆逾現有 ★ 軌道涵蓋（AUTH-WIRING 限 (a) route store／
(b) alt-login 三表單／(c) captcha；I18N-WIRING (i) 明訂「不改攔截器碼分組/logout/refresh
控制流語意」；MODAL-WIRING 限 `views/manage/**`＋user-center）：

- **(i) logout server-call 接线**：拍板7 `/auth/logout` 伺服器端撤銷，需前端 logout
  （現純 `authStore.resetStore()`、主動登出呼叫點 `src/layouts/modules/global-header/
  components/user-avatar.vue`）改為「先呼 `/auth/logout`(帶 refreshToken) 再 resetStore」。
  此點非 AUTH-WIRING(ADR 0031) 三用途任一——屬**未授權第四處 inline**（對抗式健全性審查
  抓出、brainstorm §0.1-J）。
- **(ii) 閒置登出 toast**（B-062）：攔截器 `src/service/request/index.ts`＋`src/service-alova/
  request/index.ts` 的 `logoutCodes`(8888) 靜默分支、`handleLogout()` 前插輕量 toast，逾
  I18N-WIRING (i)「不改攔截器控制流語意」紅線（L-110：upstream 只有靜默重導/阻斷 modal 兩態）。

比照 004 ADR 0028（I18N-WIRING (iv)）／005 ADR 0031（AUTH-WIRING）先例，於 006 plan
Constitution Check 觸發、走 §V.2 Amendment。

## 決定

新增 ★ 軌道 **BASE-WEB-LOGOUT-UX-WIRING**（constitution §III.2），授權且嚴格限兩用途：

- **(i)** logout server-call 接线：`user-avatar.vue` 主動登出改「呼 `/auth/logout`(帶
  refreshToken)→再 `resetStore()`」。
- **(ii)** `logoutCodes`(8888) 靜默分支登出前輕量 toast：`service/request/index.ts`＋
  `service-alova/request/index.ts` 同構、`$t(backend.auth.session.reLogin)`；★嚴格限
  「登出前顯 toast」、**不改碼分組/logout/refresh 其餘控制流**。

皆走 fork-delta `rev4-inline` 修改型（帶 `原行:`）＋ fork-delta-lint 機器強制；第三用途
→ 再 §V.2 Amendment。constitution MINOR bump（§V.3「新增 ★ 軌道」）；與 0033 §I.7
amendment 同 commit → **v1.2.0 → v1.3.0**。軌道全文入 constitution §III.2、與本 ADR 同 commit。

## 後果

- 006 plan Constitution Check Q2（動 base-web inline 有無授權用途）GATE 解除。
- toast 屬行為變更→ CDP 真瀏覽器驗（`CDP:127.0.0.1:9229`、L-053）＋ toast 項前 restart
  base-web 斷言無 raw i18n key（L-015）。
- 授權面精確限兩點、不外溢；pwd-login／auth store 其餘控制流／7777 阻斷 modal 分支（既有
  `modalLogoutCodes`）零改動。
- **未納本軌道、plan 須另定歸屬**：跨請求棧共用單一 `refreshTokenPromise`（brainstorm §5、
  防 axios＋alova 雙棧並發 refresh 誤判 reuse）動到 `service/request/shared.ts` 去重狀態，
  屬 service 層基建、非本軌道 inline 授權範圍——plan（research）定走 WRAPPER 或另議。
- fork patch set 仍全程 `rev4-inline` 可定位、upstream rebase 友善；兩處各在 spec/plan
  紀錄位置＋改動＋衝突風險。
