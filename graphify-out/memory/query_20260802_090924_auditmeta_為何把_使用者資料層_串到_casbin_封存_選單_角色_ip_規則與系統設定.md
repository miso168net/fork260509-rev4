---
type: "query"
date: "2026-08-02T09:09:24.969351+00:00"
question: "AuditMeta 為何把「使用者資料層」串到 casbin 封存、選單、角色、IP 規則與系統設定、稽核日誌端點等 12 個社群？"
contributor: "graphify"
outcome: "useful"
source_nodes: ["AuditMeta", "mutate_in_txn()", "facade/sys_operation_log.rs", "facade/sys_user.rs", "facade/sys_menu.rs", "facade/sys_role.rs", "sys_casbin_policy.rs", "facade/sys_ip_rule.rs", "facade/system_settings.rs", "audit_query.rs"]
---

# Q: AuditMeta 為何把「使用者資料層」串到 casbin 封存、選單、角色、IP 規則與系統設定、稽核日誌端點等 12 個社群？

## Answer

Expanded from original query via vocab: [auditmeta, audit, operation, log, facade, operator, trace, meta]. Traversed from AuditMeta (54 度、社群 2) and verified by four read-only lenses (anatomy/birth/breadth/readback).
AuditMeta 橋 12 社群的實質＝刻意的表中立橫切審計架構：audit.rs:64-70 定義（operator id+peer/real INET、trace_id、xff、ip_confidence），零 entity 概念，故可被使用者/角色/選單/casbin 治理/IP 規則/系統設定諸域同時消費；任何 facade 變更型寫路徑簽名必收 meta（穿透設計），全域匯入唯一 append-only sink sys_operation_log——一個 meta 型、一個事件形（AuditEvent 8 值封閉詞彙）、一個 sink、一套同交易紀律把彼此無 FK 的 entity 社群縫成同一條稽核平面。54 度＝18 檔 118 處引用；邊數正比各域寫端數（sys_user 16 最大）、非耦合異味。
誕生：audit_meta() 七 handler 檔鏡像；ctx 在場取 trust 鏈研判 IP+單一 seam 淨化的 trace_id（X-Request-Id 白名單 64 上限全有全無）；ctx 缺席各欄 None fail-open、uid 恆在。邊界：meta 豐化 fail-open（txn 外定案、缺席只損鑑識細節）vs op-log 列本體 fail-closed（mutate_in_txn 同交易、業務與稽核同生共死；對照 access_log 全 fail-open 異步觀測軌——存取軌跡是觀測、變更審計是帳）。
消費三檔次：簡單域走通用 mutate_in_txn；聚合域自管 txn 手排同序（advisory lock 首動作）；casbin 治理 facade 收 caller txn、handler finish_governed 同 txn 收尾——殊途同歸固定序「業務寫→op-log→commit」。casbin 最厚：身分蓋章雙表（op-log+歸檔 archived_by）、守門先於寫入、七步鎖序。設計內例外僅三（write_session_id/custody 側表/session_event 平行 sink），無漏稽核破口。
讀側閉環：寫側每欄讀側 DTO 皆可見（null 忠實直出不補值）、PII 打碼單點；person filter id 優先、name 解析含軟刪（稽核鏈不因刪帳號斷）；purge 自記同交易+刪 0 照記+雙自保（created_at 高於水位線+operation 不等於 PURGE 豁免）。唯二設計取捨：trace_id 等鑑識欄可見不可濾；created_by NULL 列人員過濾天然不可及。
與 AppError 脊椎互補：AppError＝所有失敗走同一扇門；AuditMeta＝所有變更蓋同一顆章。

## Outcome

- Signal: useful

## Source Nodes

- AuditMeta
- mutate_in_txn()
- facade/sys_operation_log.rs
- facade/sys_user.rs
- facade/sys_menu.rs
- facade/sys_role.rs
- sys_casbin_policy.rs
- facade/sys_ip_rule.rs
- facade/system_settings.rs
- audit_query.rs