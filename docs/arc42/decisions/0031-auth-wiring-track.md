---
id: "0031"
title: 新增 ★BASE-WEB-AUTH-WIRING 軌道（auth 刀三處 base-web inline 接线授權）
date: 2026-07-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 005-auth-login plan Constitution Check Q2/Q7（user 親決）；需求源＝ADR 0029〔alt-login stub〕＋constitution §II #2〔dynamic route〕"
tags: [constitution-amendment, fork-delta, base-web, auth]
---

## 背景

005-auth-login 交付已 accepted 的兩拍板需動 base-web 三處 inline，皆逾現有 ★ 軌道涵蓋
（MODAL-WIRING 限 `views/manage/**`＋user-center；I18N-WIRING 限攔截器/locale/Schema；
ADAPT 限 `.env*`＋`typings/api` 新檔；WRAPPER 限 `service/api/rev4-*` 新檔——皆不涵 `store/`
`hooks/` `views/_builtin/`）：

- **(a)** `src/store/modules/route/index.ts`：dynamic 模式 `getConstantRoutes` 回 `[]` →
  `addConstantRoutes([])` 丟棄前端 builtin 常數頁（login/404/403）→「No match for login」破口
  （接地實證 index.ts:160-163）。
- **(b)** `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue`：handleSubmit
  現為 `$message.success` 假成功，須改真打後端 stub 才收斂帳實。
- **(c)** `src/hooks/business/captcha.ts`：getCaptcha 現為 setTimeout 假動作，須改打 sendCaptcha
  stub。

三處皆非新功能、係把 approved 決策（ADR 0029 stub 帳實收斂＋§II #2 dynamic 落地）接到前端的
最小 inline 集。比照 004 ADR 0028（zh-tw locale 逾 I18N-WIRING (ii)→plan 期立 (iv)）之先例，
於 005 plan Constitution Check 觸發、走 §V.2 Amendment。

## 決定

新增 ★ 軌道 **BASE-WEB-AUTH-WIRING**（constitution §III.2），授權且嚴格限上述三處 inline
接线 (a)~(c)，皆走 fork-delta `rev4-inline` 修改型（帶 `原行:`）＋ fork-delta-lint 機器強制；
第四處接线 → 再 §V.2 Amendment。constitution MINOR bump **v1.1.0 → v1.2.0**（§V.3「新增 ★
軌道」）。軌道全文入 constitution §III.2、與本 ADR 同 commit。

## 後果

- 005 plan Constitution Check Q2/Q7 GATE 解除、得進 Phase 0/1。
- fork patch set 仍全程 `rev4-inline` 可定位、upstream rebase 友善；三處各在 spec/plan 紀錄
  位置＋改動＋衝突風險。
- 授權面精確擴至三點、不外溢（(a) route store 只改常數合併、(b) 只三 alt-login 表單提交、
  (c) 只 captcha 取碼）；pwd-login／auth store／攔截器控制流仍零改動。
- provenance 分流：(a)＝rev3 010 已驗證；(b)(c)＝rev4-new（ADR 0029）——未來 alt-login 做真
  （B-027/028/029/030）時 (b)(c) 為替換點。
