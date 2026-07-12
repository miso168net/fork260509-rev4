---
id: "0050"
title: 業務錯誤結構化明細通道——信封 data 欄載 i18n 插值參數（含洩漏面評估與 §I.3 讀法確認）
date: 2026-07-12
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-12 009-role-admin brainstorm D7（user 拍②結構化明細案、2026-07-11~12）＋specify 期通道實查＋plan Constitution Check Q4＋plan research R4；消化 B-047（rev3 015 遺留）"
tags: [wire, i18n, error-handling, security]
---

## 背景

rev3 的治理拒因（protected-reject、in-use 等）只回泛化訊息——facade 帶明細但 wire 不載，操作者無從自助排除（B-047）。009 守門大增（三層刪除守門、停用雙護欄、受保護拒絕、復原三態），泛化訊息的挫折面隨之放大。D7 兩案並陳後 user 拍②結構化明細案。

## 決定

**載體＝business error（HTTP 200、`code:"2222"`）信封的既有 `data` 欄**，承載該 i18n key 的插值參數物件：

- **形**：`msg`＝distinct key（一因一鍵：`biz.role.seededProtected`／`inUse`／`cannotDeleteSelfRole`／`cannotDisableSelfRole`／`superCannotDisable`／`codeImmutable`／`codeExists`／`codeInvalid`／`biz.policy.protectedRevoke`／`notRestorable`；menu-orphan 子因併用 `notRestorable`）；`data`＝參數物件（如 `{userCount:3}`、`{blocked:[{target,dimension}]}`）；前端 `$t(msg, data)` 插值。
- **§I.3 讀法確認**（plan Constitution Check Q4）：信封三欄 `{data,code,msg}` **不增不減**、`data` 型別本就逐端點自由——本通道僅使用既有自由欄、**不觸 §I.3 Amendment**。
- **後端形**：AppError 新攜參變體（`Biz(key, Option<Value>)` 形）；既有無參 `2222` 路徑**零改動**。
- **前端接線**（specify 期實查＋R4）：業務錯誤時信封整包附於錯誤物件回到呼叫端（flatRequest `{data:null, error, response}`、共用攔截層對 json 不拆信封）→ `data` 欄**不需任何攔截器改動即抵達呼叫端**（通道可達性結論）。呈現＝雙層並存：①共用層＝onError 既有 msg 顯示點單點插值擴充（`data` 為 plain object→`$t(key, detail, msg)` 三參、否則維持現行 fallback——屬顯示點插值表達式擴充、**不觸 (i) 明文禁改之碼分組／logout／refresh／retry 控制流語意**）——歸 BASE-WEB-I18N-WIRING (i) 射程（帶參 key 的「譯為在地化文字」本質含供其插值參數）、免 Amendment；②呼叫端層＝需結構化渲染者（protectedRevoke blocked 清單）於 view 局部讀 `error.response.data.data`——歸 MODAL-WIRING (a) 呼叫端邏輯。

**洩漏面評估**：

- 受眾＝R_SUPER（v1 治理寫端唯一可達角色；getRoleList／getAllRoles 兩條多角色讀端無明細參數需求）。
- 內容邊界＝**該受眾本可經既有查詢能力自查的資訊**（掛載人數可由 user 列表數、被擋 policy 清單可由三維讀端自查）→ **零新增洩漏面**。
- ★**下放重評觸發**：任何寫端授權下放非 super 之前，MUST 連動重評明細通道的受眾邊界（與 M-6 no-escalation 前置同綁一條 BACKLOG 條目）——明細內容的「自查等價」前提隨受眾改變即失效。

## 後果

- B-047 消化（收刀時 BACKLOG 刪列）；spec FR-033~036 的落地依據。
- 攔截器擴充落在 004 已標 `rev4-inline` 修改型塊上（provenance 追加 009、`原行:` 不變）；vue-i18n 三參 overload 對非 scalar named 值的渲染行為 impl 期 CDP 實跑驗證。
- key 形紀律（★本 ADR 新增紀律主張、親決即拍板）：message 僅 scalar 佔位（物件/陣列類 data 走呼叫端結構化渲染、不進 `$t` 插值）——無機器 lint、靠 spec 驗收與 review 守；驗收字面落 tasks T031（字典撰寫時逐鍵核）。
