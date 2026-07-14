---
id: "0058"
title: 稽核 purge 執行面——時間水平線唯一形狀、下限守門、自落 op-log；保留天數政策 B-016 續留
date: 2026-07-14
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-14 012-audit-admin brainstorm（user 親決 D4；D1 access-log 全做使四表單調成長、purge 升級為本刀必答）；rev3:B-039「purge 執行面於審計功能刀 schema 期」＋B-016「retention 政策 v1 只容量監控」切分（ADR 0011 內文）"
tags: [audit, purge, retention, append-only, backlog]
---

## 背景

四張稽核表（sys_operation_log／sys_access_log／sys_login_attempt／session_event）皆
append-only 單調成長；D1 拍定 access-log 寫入端啟用後量級直接上門。rev3 結論把 purge 拆兩半：
執行面（機制）排審計功能刀 schema 期（B-039）、retention 政策本體（保留多久）等容量警示再拍
（B-016）。另有憲法張力：§I.6 變體 B「append-only 不可竄改」——purge 若可挑列刪，超管即可
選擇性滅證，稽核完整性破功。

## 決定

- **本刀建 purge 執行面、政策不拍**：`POST /systemManage/purgeAuditLog`（僅超管、casbin seed
  隨本刀 migration）；參數 `{table, beforeDays}`、table 限四稽核表枚舉白名單。
- **時間水平線唯一形狀**：`DELETE WHERE created_at < now() - beforeDays`——構造上不可能挑列刪。
  水平線 retention 刪除**不屬**變體 B 所禁之「竄改」；入憲（島 J 候選 J3）時同步收斂措辭。
- **下限守門**：beforeDays 下限 30 天、server 常數寫死（防手滑清近期紀錄）；保留天數政策與
  自動化排程續留 B-016（容量警示時再議）。
- **purge 自落 op-log**：`AuditOperation` 新增 `Purge`（"PURGE"）、payload＝
  {table, before_days, deleted_count}——刪過什麼範圍永遠有案可查；水平線語意下新列
  created_at=now 恆不落入自身刪除範圍。
- UI＝每 tab 清理鈕→modal 輸入天數＋二次確認；拒因走 backend.biz.audit.* 結構化明細三語。

## 後果

- B-039 的 purge 半邊隨本刀兌現（pg_trgm 半邊歸 ADR 0057）；B-016 續留、觸發不變。
- 未來自動化 purge（排程/TTL）落地時 MUST 複用本執行面的水平線語意與 op-log 自記，禁止另闢
  挑列刪路徑；政策落地＝B-016 兌現時立其 ADR。
- 手動 purge 為稽核表上唯一刪除路徑；任何選擇性刪列需求＝翻案本檔（新 ADR supersede）。
