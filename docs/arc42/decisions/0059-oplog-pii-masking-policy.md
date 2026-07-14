---
id: "0059"
title: op-log payload PII 政策——落庫白名單定調＋讀端顯示面打碼（收 B-044）
date: 2026-07-14
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-14 012-audit-admin brainstorm（user 親決 D5＝顯示面打碼、不取落庫遮蔽/不遮兩案）；rev3:B-044「op-log payload PII 遮蔽策略先拍再落庫」（K2-29）；實查＝sys_user AuditSerialize 白名單（password/session_id 永不入列、t009_* 負向自證）而 user_phone/user_email 在列、011 起既成落庫"
tags: [audit, pii, masking, oplog, backlog]
---

## 背景

B-044（rev3）要求 op-log payload 的 PII 遮蔽策略「先拍再落庫」；實況是 011 起 payload 已在
落庫：最敏感兩樣（password argon2 PHC、session_id）已被白名單逐欄手構結構性封死（島 I5、
負向自證塞入即紅），但一般個資（user_phone/user_email/nick_name/user_memo）隨快照完整入列。
audit UI 僅超管可見，且超管在使用者管理頁本可見電話/email 全值；audit 讀端把 payload 首次
搬上管理介面，顯示層級的遮蔽需求由 user 親決。

## 決定

- **落庫面定調現況＝政策**：白名單逐欄手構（密碼明文/雜湊、會話識別永不入列＝島 I5 底線）即
  落庫遮蔽策略本體；一般個資完整落庫、保留 before/after 快照的救援價值。不回溯清洗既有列。
- **顯示面打碼（D5 親決）**：audit 讀端於**後端**遮蔽後才上 wire、前端不經手原值——key-based
  掃 payload JSON（payload_before/payload_after 兩側、對任何 entity_table 通用）之
  `user_phone`／`user_email` 鍵：電話留前 3 後 2、中段固定 `****` 不保留原長度
  （`0912345678 → 091****78`）、email local-part 留首字元＋固定 `***`、domain 全留
  （`andy@example.com → a***@example.com`）。
- 遮蔽單點＝讀端序列化處恰一處（島 J 候選 J4）；負向自證＝讀端回應含原值即紅。

## 後果

- B-044 收口（收刀時刪列）；既有落庫列零改動、零 migration。
- 打碼僅及 audit 讀端顯示——使用者管理頁等既有介面的個資顯示權限語意不變（同一超管兩頁所見
  不同＝有意識接受：audit 頁定位為可長期翻閱/未來可能下放的報表面、防旁窺基線較高）。
- 遮蔽鍵清單（user_phone/user_email）為白名單常數；新增遮蔽鍵＝改常數＋補測試、不需翻案；
  改變遮蔽方向（如取消打碼或落庫遮蔽）＝新 ADR supersede 本檔。
