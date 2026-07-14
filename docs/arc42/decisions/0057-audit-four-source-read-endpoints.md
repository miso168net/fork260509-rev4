---
id: "0057"
title: 稽核讀端四源＋查詢能力——兌現並增補 ADR 0011（三表→四源、pg_trgm 本刀落地）
date: 2026-07-14
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-14 012-audit-admin brainstorm（user 親決 D2/D3；偵察＝m002 三支 GET seed 已預埋、session_event 五事件有寫零讀）；rev3:ADR 0011 母體（三表讀端＋僅超管 read-only）"
tags: [audit, read-endpoints, session-event, pg-trgm, backlog]
---

## 背景

ADR 0011（rev3）拍定稽核三表（操作／存取／登入嘗試）補查詢讀端＋僅超管 UI、read-only
reporting、刻意殿後；m002 已 seed `manage_audit` 選單與三支 GET 端點的 casbin 授權，但
router 零註冊＝讀端全新地。偵察另發現 session_event（kicked/revoked/logout/idle/reuse
五類會話終止事件）有真實寫入但不在三表拍板內、亦無讀端授權——查「這帳號 session 為什麼斷」
時，op-log 只有管理動作那半（KICK/RESET），系統自動事件（idle/reuse/logout）只在 session_event。
模糊搜尋（帳號名/路徑部分比對）為 log 查詢主菜，B-039（rev3）已預拍「pg_trgm 於審計功能刀
schema 期落地」。

## 決定

- **四源讀端**（012 刀交付）：`getOperationLog`／`getAccessLog`／`getLoginAttempt`（端點名照
  m002 seed 既定）＋新 `getSessionEvent`（casbin seed 隨本刀 migration 補列）。本檔對 ADR 0011
  為**增補**（三表→四源）、非翻案——0011 的僅超管、read-only、UI 定位全數沿用。
- **查詢能力 v1**：全表共通時間區間＋分頁（對齊 getUserList 範式）；各表專屬精確 filter；
  模糊搜尋兩欄＝`sys_login_attempt.attempted_user_name`＋`sys_access_log.http_path`，
  索引照 B-039 rev3 結論本刀 schema 期落 pg_trgm GIN（op-log payload jsonb 搜尋不做、YAGNI）。
- UI＝「稽核中心」一頁四 tab（`/manage/audit`、MODAL-WIRING(e) 建頁、兌現 B-061 audit 項）。

## 後果

- session_event 讀端授權＝新增 casbin seed 一列（ADR 0032 新增放寬軌道）；gate2 期望值同步。
- B-039 的 pg_trgm 半邊隨本刀兌現（purge 半邊歸 ADR 0058）；收刀時 B-039 刪列。
- 讀端 payload 顯示遮蔽歸 ADR 0059；access-log 資料源啟用歸 ADR 0060。
- 若未來需第五資料源（如 sys_token 狀態機檢視），擴充＝立新 ADR、不改本檔。
