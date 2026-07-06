---
id: "0036"
title: FR-017(ii) service-alova 閒置 toast 副本 by-design 省略（alova 對真實 auth dormant＋既有 showErrorMsg 雙彈＋乾淨做須動 showErrorMsg 出軌道）
date: 2026-07-06
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-06 006-session-lifecycle final holistic review（T038）鏡頭①③ 判 FR-017(ii) 半實作（M1/M4 major）；U11 act-on-code 接地＋U11 spec review 已核可 alova 省略；user 親決 2026-07-06（(A) 立 ADR）"
tags: [fork-delta, base-web, i18n, session, wont-fix]
---

## 背景

FR-017(ii)／tasks T030／憲法 §III.2 ★BASE-WEB-LOGOUT-UX-WIRING (ii)（ADR 0034）三處皆逐字要求：
閒置登出 toast「含 `service/request/index.ts` **與** `service-alova/request/index.ts` 兩同構副本」——
於各棧 `logoutCodes`(8888) 靜默分支 `handleLogout()` 前顯 `$t(backend.auth.session.reLogin)`。

U11 實作僅交付 axios 棧（`service/request/index.ts`）一份，**未**動 `service-alova/request/index.ts`。
006 final holistic review（T038）鏡頭①③ 將此判為 major（FR-017(ii) 半實作、無 ADR 背書）。

實作期 act-on-code 接地（U11）確立三事實：
1. **alova 棧對真實 auth 流 dormant**：真實 login／getUserInfo／getUserRoutes／全部 manage CRUD／
   會 401→8888 換發之請求**全走 axios 棧**；`service-alova` 全 repo 僅 5 個 `views/alova/*` demo 頁
   import（見 ADR 0035 §背景1）。真實使用者 session 過期**不經** alova 路徑。
2. **alova `handleLogout()` 已含 `showErrorMsg(state, message)`**（≠axios 棧之純 `resetStore()` 靜默）：
   其 `logoutCodes` 分支本就顯一則訊息；再前插 `reLogin` toast＝**雙彈**（兩則訊息）。
3. **alova `onError` 之 `message=data.msg` 未經 BASE-WEB-I18N-WIRING $t 轉譯**（既有 gap、非本刀引入）：
   其 `showErrorMsg` 顯示的是**原始 backend msg key**（如 `auth.session.reLogin` 字面），非譯文
   「請重新登入」。於此再加 reLogin toast，使 demo 路徑同時出現「一則 raw key＋一則 reLogin toast」，
   體驗**更差**。

## 決定

**FR-017(ii) 之 `service-alova` 副本 by-design 省略**（不交付第二份 toast 副本、不改
`service-alova/request/index.ts`）。真實閒置 UX 由 axios 棧 idle toast 交付（U11、已驗 typecheck/build/
fork-delta-lint、runtime 由 CDP-2/T036 驗）。

理由：
- alova 對真實 auth dormant（事實1）：真實 session 過期不走 alova、SC-004／CDP-2 由 axios 副本滿足。
- 加 alova toast 與既有 `showErrorMsg` 雙彈（事實2）、且疊在未 $t 的 raw key 上使 demo 路徑更差（事實3）。
- 要「單彈且正確」必須動既有 `showErrorMsg`（改其顯示/抑制）＝逾 LOGOUT-UX-WIRING（ADR 0034，限「登出
  前顯 toast、★不改 logout 其餘控制流」）與 I18N-WIRING（ADR 0028，(i) 明文「不改攔截器 logout 控制流
  語意」）兩軌道紅線 → 須另立 §V.2 Amendment。為一條 dormant demo 路徑付 Amendment＋動 refresh/logout
  控制流，投報比極低（與 T034／ADR 0035 之 alova-dormant 判斷一脈相承）。

## 後果

- **真實 UX 不受影響**：真實使用者閒置逾時走 axios 棧→顯 reLogin toast 後重導（SC-004／CDP-2）。
- **alova demo 路徑維持既有行為**：其 `logoutCodes` 分支仍由既有 `showErrorMsg` 顯一則（raw key）訊息、
  未新增雙彈；此 raw-key i18n gap 為既有、非本刀引入、僅影響 5 個 demo 頁。
- **觸發再議條件**：若日後將 `service-alova` 棧接入真實 auth 流（同 ADR 0035 觸發條件），屆時一併補
  alova idle toast＋修其 onError i18n（$t 轉譯）＋處理雙彈（可能需軌道 Amendment）。列 BACKLOG 追蹤。
- **as-built vs spec**：本 ADR 記錄 FR-017(ii) 之 alova 副本 by-design 省略（實作結果偏離 spec 「兩同構
  副本」字面；spec/tasks 文字不回改，權威以本 accepted ADR 為準，憲法 §V.1）。
