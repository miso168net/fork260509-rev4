---
id: "0060"
title: sys_access_log 寫入端啟用——protected 全請求、fail-open、不記 body/query
date: 2026-07-14
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-14 012-audit-admin brainstorm（user 親決 D1＝全做、不取空表上架/整包延後兩案）；偵察＝sys_access_log entity＋schema＋casbin seed（m002:345）齊備但零 facade 零寫入端＝零流量表；rev3:ADR 0011 三表讀端含存取日誌"
tags: [audit, access-log, middleware, fail-open]
---

## 背景

sys_access_log（archetype B append-only、12 欄）自 m001 建表即備妥，m002 亦 seed 了
`getAccessLog` 讀端授權，但全庫零寫入端＝永遠空表。ADR 0011 三表讀端含存取日誌；不補寫入端
則讀端與 UI 分頁形同虛設。表上 created_by NOT NULL 的既定形制天然限定「已認證請求」——
公網未認證流量不在此表射程（登入行為歸 sys_login_attempt 管、不重疊）。

## 決定

- **寫入端＝axum layer 掛 protected 路由群**（012 刀交付）：已認證請求每 request 落一列，
  response 完成後寫。
- **欄位**：http_method／http_path／http_status＋IP 信任錨四欄（real/peer/xff/confidence、
  島 F4）＋region（GeoIP best-effort、沿 ADR 0046）＋trace_id。
- **best-effort fail-open**：寫失敗只 warn、絕不擋業務請求（對齊島 E1/F3「稽核寫故障
  fail-OPEN」精神；入憲候選 J2）。
- **不記 request body／query string**——零 PII 入列、免遮蔽問題（顯示面遮蔽議題因此不及於
  本表）；audit 自家讀端請求照記（一致性、無豁免名單）。

## 後果

- 存取軌跡自本刀起真實累積；量級＝每已認證請求一列，purge 執行面（ADR 0058）同刀就位、
  容量監控續留 B-016。
- http_path 模糊搜尋之 pg_trgm GIN 索引隨本刀 migration 落地（ADR 0057）。
- 若未來需記 body/query（如除錯場景），因涉 PII 落庫＝翻案本檔（新 ADR supersede）並先過
  遮蔽策略（ADR 0059）擴充。
- 若未來公開面（未認證）存取記錄需求出現＝另表另 ADR，不動本表 NOT NULL 形制。
