---
id: "0076"
title: 稽核 retention 自動清理——遵憲 J3 自記＋reaper 權限最小擴張（B-016 本體、兌現 0075 預留條款）
date: 2026-07-21
status: draft
supersedes: ["0075"]
superseded_by: []
provenance: "rev4:2026-07-21 017-audit-retention brainstorm——user 親決 Q1（env 四鍵無 UI）/Q2（遵憲自記、經批判複審翻案重拍）＋批判複審 4 調整全收；research R1（告警射程收斂新發現）/R8（自記 payload 形）落定；上游＝ADR 0075（預留條款「retention 刀再議」即本刀）"
tags: [audit, background-job, retention, obs, security]
---

## 背景

016 對稽核四表（sys_operation_log／sys_access_log／sys_login_attempt／session_event）只落了
容量告警④、無自動清理——資料生命週期半開（012 僅管理端手動 purge）。ADR 0075（B-067
by-design 收單）明文「不新增任何自動刪除」「reaper 刪除範圍明確不含 session_event」，並預留
「未來 retention 政策刀再議自動化、屆時本 ADR 為現行準據」。B-016 本體即該預留時刻。
憲法島 J3（v1.10.0 入憲）：稽核資料唯一刪除形狀＝表白名單×天數水平線；每次 purge MUST
同交易自落操作稽核（0 列照落）；op-log 源固定豁免 PURGE 列；拆自記＝MAJOR——射程無
「管理端」限定、涵蓋自動刪除。承襲基底＝016 reaper 底座（`--job` 擴充位、dry-run/execute
雙姿態、失敗不推心跳、pushgateway 心跳＋告警⑤/⑤b）＋012 purge 執行面（四表封閉白名單、
`PURGE_MIN_DAYS=30`、`purge_before` facade、同交易自記機制）。

## 決策

新增 reaper job `audit-retention`（sidecar loop 每輪 token-reap 後接跑、失敗互不阻斷），
決策叢六項：

1. **遵憲 J3 自記**：execute 每表單交易 {水平線 DELETE＋PURGE 操作稽核自記}；刪除筆數
   0 列照落；dry-run 不自記（零變動觀察姿態）。「同交易」義務射程＝單表刪除×自記對——
   跨表非原子、逐表獨立交易、部分完成＋整體報錯＋下輪冪等。★重拍紀錄：原拍「不自記、
   純觀測軌跡」經批判複審判違憲（J3「每次 purge MUST 同交易自記」＋「拆自記＝MAJOR」）
   翻案；修憲限縮 J3 路線（MAJOR bump）成本效益不成比例、落選——自記累積實際日 4 筆、
   年約 0.5MB、可忽略。
2. **reaper 權限最小新增擴張**（m013 純 GRANT、零表結構 DDL）：恰好集＝四稽核表
   SELECT,DELETE＋sys_operation_log INSERT（自記）＋SEQUENCE sys_operation_log_id_seq
   USAGE（自記 INSERT 之 nextval）；不新增四表 UPDATE 與白名單外任何表之權（越權由 DB
   權限拒絕）。落選：另建第二 role 隔離 retention 身分——同一 sidecar 同一連線 secret、
   切 role 徒增輪替面。
3. **系統操作者表示法**：自記列 `operator=None`→`created_by NULL`（schema nullable、機制
   現成、零 schema 變更）＋payload `{table, before_days, deleted_count, job:"audit-retention"}`
   （前三欄與手動 purge 逐字同形、`job` 欄自動列獨有）；讀端零改動、操作者欄空白呈現——
   區分徑三重＝PURGE 類型＋操作者空＋payload `job` 欄。落選：合成哨兵 uid（0/-1）——污染
   enrich 語意、schema 本支援 NULL；operation 新詞彙 `AUTO_PURGE`——動 AuditOperation 枚舉
   與 DB 欄寬契約、且 J3 豁免以 `operation='PURGE'` 字面錨定、自動列必須同詞彙才被豁免保護。
4. **env 四鍵三分語意**：`AUDIT_RETENTION_{OPERATION_LOG,ACCESS_LOG,LOGIN_ATTEMPT,SESSION_EVENT}_DAYS`
   逐表可調、無 UI（Q1 拍板；落選 system_settings 存放／專屬 admin UI）；缺席→預設 90 照跑
   ／畸形（無法解析為非負整數）→warn＋90 照跑／在場低於 30 含 0（下限鏡像 `PURGE_MIN_DAYS`、
   不 clamp）→開跑前整體拒絕（結構化 error＋非零退出＋四表零刪除＋不推心跳）。★刻意
   不對稱：畸形＝無意圖噪音退預設；明確設低於下限＝人為意圖但違規——系統不猜、零動作
   （「部分表照跑＋報錯」不採、行為最可預測）。
5. **告警⑥/⑥b 成對新增＋⑤/⑤b 射程收斂 matcher**（research R1 接地新發現）：prometheus
   對 pushgateway `honor_labels: true`＝grouping key label 全保留，既有⑤/⑤b expr 無 job 維
   matcher——audit-retention 心跳進場後會被⑤誤掃（射程重疊）。故⑤/⑤b 同 commit 補
   `reaper_job="token-reap"`、新增⑥（audit-retention 心跳逾時、門檻沿 172800＝2×86400
   互錨）與⑥b（dry-run 在場而 execute 缺席＝誤配）鏡像⑤/⑤b 全結構；告警④（容量）退為
   backstop、規則不動。
6. **心跳 `reaper_job` 分組＋一次性清舊組遷移**：兩 job 各自 grouping key
   `/metrics/job/reaper/reaper_job/<job>`（pushgateway PUT＝整組替換、同組先後推會互清對方
   心跳）；token-reap 心跳 URL 同步遷移。升級附人工一次性步驟：`DELETE /metrics/job/reaper`
   清無 reaper_job label 之舊組→兩 job 各跑一輪 execute 重建健康心跳（操作文件承載、不另建
   自動化）。落選：獨立 job 名分組（`/metrics/job/reaper-audit`）——metric 名相同仍被無
   matcher 的⑤掃到、且失去 `job="reaper"` 家族聚合。

**翻案面（supersede 0075）**：0075「不新增任何自動刪除」「reaper（ADR 0072）刪除範圍明確
不含 session_event」就此翻案——本刀以遵憲形（J3 白名單×水平線＋同交易自記）新增自動刪除、
reaper 射程擴及 session_event 在內的稽核四表；0075 預留條款「未來 retention 政策刀再議
自動化、屆時本 ADR 為現行準據」即本刀兌現；0075 的能見度閉環（容量監控＋手動 purge 端點）
不廢除、續為 backstop。

## 後果

- B-016 收單（收刀時 BACKLOG 刪列）；稽核四表尺寸有界（預設 90 天水平線）。
- 憲法零 amendment（島 J3 逐條對齊；reaper 以遵憲形進入 J3 射程）。
- 首跑／調小天數後的巨量刪除＝單語句大交易，v1 有意識接受；prod 部署刀前重估批次化。
- session_event 水平線謂詞退全表掃描（僅 (user_id, created_at) 複合索引）——dev 量級接受、
  不補索引（守「零表結構 DDL」）、prod 前與批次化一併重估。
- RUNBOOK 連帶：§4 env 四鍵表／§5 pushgateway 毀後重建兩 job 心跳／§8 手動姿態命令形＋權限
  恰好集／§9 清組射程＋一次性遷移／§10 重掛 GRANT 錨擴寫（m013 增量）。
