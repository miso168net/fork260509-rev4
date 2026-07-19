---
id: "0072"
title: 背景 job 底座三紀律＋首發 reaper（B-063 sys_token 回收、B-040 最小權限憑證預設）
date: 2026-07-19
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-19 016-observability brainstorm——user 親決 D8/D10；NOTES 既定「首個背景 job 設計期觸發 B-040」兌現；審查 C2 兩讀堵死＋審查 D2 安全論證更正版"
tags: [obs, background-job, security, session, deployment]
---

## 背景

sys_token 無全域回收路徑（prune_expired_rotated 僅同 chain refresh 時觸發、012 purge 四表
白名單不含 sys_token）＝過期列永留。rev4 首個背景 job 落地，依既定拍板同刀觸發 B-040
（背景 job secret 最小權限＝部署設計預設而非 prod 硬化補丁）。rev3 cleanup-job 為已驗證
母版（profile 閘門 one-shot、dry-run 預設、完跑推 pushgateway）。

## 決策

- **job 底座三紀律（ADR 級、不入憲不立島——單一 job 不夠格、維持憲法收斂）**：
  ①dry-run 預設（`--execute` 才真刪）②最小權限 DB 憑證預設 ③心跳必推（pushgateway）。
- **reaper 形**：server crate one-shot bin＋compose sidecar `profiles:[jobs]` sleep-loop 每日；
  **sidecar command 明文帶 `--execute`**（dry-run 屬手動驗證姿態、杜絕「常駐 dry-run 靜默
  no-op」兩讀）；心跳帶 mode label、**心跳超時告警只認 mode=execute**；失敗＝非零退出＋不推
  心跳→告警接手。`--job` 參數預設 `token-reap` 留第二 job 擴充位。
- **刪除判準**：刪「expires_at（refresh exp）已過超過寬限期 G（預設 7 天、env 可調）」之列、
  三類 status 統一適用；**未過期列不分 status 絕不刪**。安全論證（審查更正版）：過期列不可達
  的實際成立腿＝jwt verify 先拒過期 access（前提 access TTL 遠小於 G、調至天級需重核）——
  denylist PG fallback（has_active_in_chain）只濾 status 不濾 expires_at、不可倚賴；revoked／
  rotated 未過期列的運行時依賴在 refresh 端點（reuse 偵測、kicked 分支、session_event 稽核）。
- **B-040**：專屬 reaper DB user 權限僅 sys_token 之 SELECT＋DELETE；secrets 新增
  `reaper_password` leaf＋`reaper_database_url` composite（由 leaf 組合、沿 generate-secrets
  慣例）；role 建立與設密機制 plan 期拍、原則定死＝**密碼絕不進 migration、絕不進 git**。

## 後果

- B-063／B-040 收單；sys_token 表尺寸有界。
- 未來背景 job（含 B-100 軟刪掃描若以第二 job 形落地——此為詮釋連結非其條目本文）沿用
  三紀律與 `--job` 底座。
