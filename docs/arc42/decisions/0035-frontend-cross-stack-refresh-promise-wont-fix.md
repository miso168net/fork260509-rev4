---
id: "0035"
title: T034 前端跨棧共用 refresh 在途承諾 won't-fix（by-design：alova 對真實 auth dormant＋後端 grace 冪等為並發正確性防線）
date: 2026-07-06
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-06 006-session-lifecycle 實作期（U11 base-web 前）act-on-code 接地；research R2 定調前端共用 promise「為輔、非正確性依賴」＋tasks T034「WRAPPER 新檔優先、若須動 shared.ts inline 另評軌道」；user 親決 2026-07-06"
tags: [fork-delta, base-web, auth, session, wont-fix]
---

## 背景

tasks T034（源 research R2）要前端跨棧共用單一 refresh 在途承諾：讓 `src/service/request`
（axios `@sa/axios`）與 `src/service-alova`（alova）兩攔截器共用同一個 in-flight
`refreshTokenPromise`，避免雙請求棧各自觸發並發換發同一枚 refresh 憑證。plan 將「軌道歸屬」
留待實作期定（「優先走 BASE-WEB-WRAPPER 新檔、零 inline；若不可避免須動 `shared.ts` inline
才另評軌道」）。

U11（base-web）施工前 act-on-code 接地，揪出三個決定性事實：

1. **app 對真實 auth／會 401→refresh 的請求實際為單棧（axios）**：auth store（login/
   getUserInfo）、route store（getUserRoutes/…）、captcha、全部 `views/manage/**`、login
   modules 等會觸發換發的請求**全走 axios 棧**；`service-alova` 對真實 auth 流 **dormant**，
   全 repo 僅 5 個 `views/alova/*` demo 頁 import 它，無任何 store／auth／route／真實業務
   view 引用。→ **「跨棧並發 refresh」在現況 app 實務上不發生**。

2. **真正的並發（雙分頁、網路重試）非前端 in-memory promise 所能救**：兩個瀏覽器分頁＝兩個
   獨立 JS 執行環境，記憶體裡的 promise（含任何跨棧共用版本）彼此不可見；此類並發由**後端
   grace 冪等快取**接住（ADR 0033 島 B1、U5 交付：同一枚有效票並發呈遞→一成功、另一 grace
   命中冪等回既發後繼、family 不撤；SC-001／CDP-3 驗）。前端共用 promise 僅 research R2 明列
   「**為輔、降頻、非正確性依賴**」。

3. **「真正跨棧共用」無法零 inline 達成**：WRAPPER 新檔（`rev4-*`）可持有 module-level
   promise，但要接通兩棧觸發點，必須 inline 改 `src/service/request/shared.ts`（axios 的
   `handleExpiredRequest` refresh 去重）＋`src/service-alova/request/index.ts`（alova 的
   `tokenRefresher`）——此二處屬「refresh 控制流」，逾全部三★軌道：LOGOUT-UX-WIRING（ADR
   0034，限 logout/toast）與 I18N-WIRING（ADR 0028，(i) 明文「不改攔截器碼分組/logout/
   refresh/retry 控制流語意」）**明文排除** refresh 控制流；AUTH-WIRING（ADR 0031）不涵蓋。
   → 若走 inline，須新 §V.2 Amendment（新★軌道或擴權）。

## 決定

**T034 判 won't-fix / by-design**：本刀**不**實作前端跨棧共用 refresh 在途承諾、**不**開軌道
Amendment。前端 refresh 並發依現況——axios 單棧自去重（手寫 `state.refreshTokenPromise`＋
1s 清）、alova 框架序列化（`createServerTokenAuthentication` 內建排隊）；並發正確性由後端
grace 冪等快取保（ADR 0033 島 B1）。

U11（base-web）僅做 BASE-WEB-LOGOUT-UX-WIRING（ADR 0034）授權之兩用途：(i) logout server-call
接线、(ii) 閒置登出 toast；**不**觸 `shared.ts`／alova refresh 去重之 inline 改動。

## 後果

- **尾巴（有界、現況不觸發）**：雙棧同時換發過期時，理論上前端可能各打一次 `/auth/refreshToken`
  ——但 alova 對真實 auth dormant，現況 app 不觸發；即便未來觸發，後端 grace 冪等吸收（第二枚
  走冪等回既發後繼、不重 rotate、不撤 family），使用者零感知、**零正確性風險**。
- **雙分頁／重試並發**：由後端 grace 保（ADR 0033 島 B1、非本 ADR 範圍）；前端任何 in-memory
  promise 皆無能為力，故不以「缺 T034」記帳。
- **觸發再議條件**：若日後將 `service-alova` 棧接入真實 auth 流（使跨棧並發成真），再評估
  「WRAPPER 新檔＋兩棧 inline」路線並走 §V.2 MINOR Amendment（新★軌道/擴權）。列 BACKLOG 追蹤。
- **as-built vs 拍板**：本 ADR 為 by-design 拒作決策（tasks 面），非推翻既有拍板；research R2
  「前端共用為輔、非正確性依賴」之定調據此坐實為「本刀不作」。
