---
id: "0040"
title: 新增 ★BASE-WEB-LOGIN-CAPTCHA-WIRING 軌道（密碼登入表單圖形驗證碼接线，嚴限一用途）
date: 2026-07-10
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-10 007-login-throttle brainstorm 拍板 6/9＋plan Constitution Check Q2/Q7（user 親決 2026-07-10）；需求源＝CAPTCHA 軟區（ADR 0037 §B）之前端接线"
tags: [constitution-amendment, fork-delta, base-web, auth, captcha]
---

## 背景

007 的 CAPTCHA 軟區（ADR 0037 §B）要求密碼登入表單在「軟區觸發」時條件渲染圖形驗證碼。此改動需動
`base-web/src/views/_builtin/login/modules/pwd-login.vue` inline，**逾現有四★軌道涵蓋**：

- **AUTH-WIRING**（ADR 0031）三用途限 (a) route store 常數合併修／(b) alt-login **三**表單 stub
  （`code-login`/`register`/`reset-pwd`，**不含 pwd-login**）／(c) 簡訊 captcha stub——無圖形驗證碼 UI。
- **I18N-WIRING** (i) 明訂「僅 msg→`$t` 最小接線、**不改攔截器控制流語意**」。
- **MODAL-WIRING** 邊界限 `views/manage/**`＋user-center 樹外例外。
- **LOGOUT-UX-WIRING**（ADR 0034）嚴限兩用途（logout server-call／靜默分支 toast）。

★另有一項**必要的連帶接线**（plan research R12 揭露）：`locked` 與 `captchaRequired` 兩態同為 `2222`、
**僅 `msg` 相異**，而 `authStore.login` 僅回 `{ data, error }`、**吞掉了 `msg`**；攔截器的 `$t` 分支結果只進 toast、
不回傳呼叫端。pwd-login 若無法取得 `msg`，即無從區分「已鎖定」與「需驗證碼」兩態、條件渲染無法成立。

★`pwd-login.vue` **現無任何 `rev4-inline` 標記**（005 刀未觸此檔）——本刀為其**首個 fork-delta**。

比照 004 ADR 0028（I18N-WIRING (iv)）／005 ADR 0031（AUTH-WIRING）／006 ADR 0034（LOGOUT-UX-WIRING）先例，
於 007 plan Constitution Check Q2/Q7 觸發、走 §V.2 Amendment。

## 決定

新增 ★ 軌道 **BASE-WEB-LOGIN-CAPTCHA-WIRING**（constitution §III.2），授權且**嚴格限一用途**：

- **(i) 密碼登入表單的圖形驗證碼接线**：`views/_builtin/login/modules/pwd-login.vue` 於收到「需要驗證碼」
  回應（`2222` ＋ `auth.login.captchaRequired`）時，條件渲染驗證碼圖與輸入欄；支援**點圖換題**、
  **帳號名變更時重新取題**、**答錯後自動重取新題**（提交即消耗、舊題已失效）。
  **含其資料取得所需之最小 store/service 接线**——使 pwd-login 能取得後端 `msg` 以區分 `locked` 與
  `captchaRequired` 兩態。

**紀律**：

- 嚴格限此一用途，絕不擴張到其他 inline 邏輯；第二種用途 → §V.2 Amendment。
- ★**不改攔截器的碼分組／logout／refresh／retry 控制流語意**（`2222` 走既有一般錯誤提示通道）；
  **`.env` 三個碼分組清單不動**。
- 走 fork-delta `rev4-inline` 紀律＋`tools/fork-delta-lint` 機器強制：修改型帶 `原行:`（`<script>` 區用 `//`、
  ★**`<template>` 區用 `<!-- [rev4-inline …] 原行: … -->`**）；新增型走圈界標記。
- 新 typing 與 service wrapper 走既有預設軌道（ADAPT 新 `.d.ts` declaration merging、WRAPPER `rev4-*.ts` 新檔），
  **不動凍結的 `typings/api/auth.d.ts`**。
- 每改一處在 spec／plan 內紀錄（位置＋改動內容＋upstream 衝突風險評估）。

constitution MINOR bump（§V.3「新增 ★ 軌道」）；與 ADR 0037 的 §I.7 島 E amendment **同一 commit**
→ **v1.3.0 → v1.4.0**。軌道全文入 constitution §III.2、與本 ADR 同 commit。

## 後果

- 007 plan Constitution Check **Q2／Q7 GATE 解除**（Q9 由 ADR 0037 的島 E 進場解除）。
- `pwd-login.vue` 自本刀起帶 fork patch，upstream rebase 時須依 `原行:` 註解對照解衝突。
  ★`<template>` 區的 HTML 註解標記在 base-web **尚無現存實例**（`fork-delta-lint` 支援但未實測）
  ⇒ 實作期首次改動後即跑一次 lint 驗證，避免標記形制退化。
- 驗證碼 UI 屬行為變更 → CDP 真瀏覽器驗（`CDP:127.0.0.1:9229`、L-053）；新 i18n 鍵加入後**前置 restart base-web**、
  斷言頁面無 raw i18n key（L-015）。★CDP **不驗證「答對」路徑**（答案不可自 challenge 還原、瀏覽器端無從取得），
  答對路徑由後端整合測試以自簽 challenge 覆蓋。
- 授權面精確限一用途、不外溢：`code-login`／`register`／`reset-pwd` 三表單、攔截器碼分組、
  `7777` 阻斷 modal 分支、`8888` 靜默分支 皆零改動。
- `authStore.login` 的最小回傳擴充落在本軌道邊界內；其**具體形**（改 store 回傳／改呼新 wrapper／
  自 `error.response` 直讀）於實作期先驗後定，三案皆不逾本軌道文字。
