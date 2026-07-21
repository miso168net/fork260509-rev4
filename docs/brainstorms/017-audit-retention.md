# 017-audit-retention 階段 0 brainstorm — 稽核 log retention 自動清理（B-016 本體）

- 日期：2026-07-21
- 方法：接地偵察（reaper bin／audit purge facade／四表 schema／告警④／m012／ADR 0075／憲法島 J3）
  → 拍板題逐題親決（Q1 設定存放、Q2 稽核軌跡）→ 模型切換後批判複審（抓到 Q2 原拍違憲＋4 處
  設計調整）→ Q2 重拍 → 交 user 審。ADR draft（§5 候選）於 user 審後隨收尾 commit 立。
- 存在理由：user 拍板 2026-07-21——下一波＝B-016 稽核 retention 政策本體（閉環 016：告警④
  容量監控已落、僅手動 purge、無自動清理）。auth／prod 組維持先前拍板後移。
- 承襲基底：016 reaper 底座（`--job` 擴充位＝B-100 留位、sidecar loop、心跳／⑤／⑤b 慣例）＋
  012 purge 執行面（四表白名單、`PURGE_MIN_DAYS=30`、`purge_before` facade、憲法島 J3）。
- 下一步：本檔 commit 落 default（rev4-admin-root）→ user 審 → ADR draft＋簿記 → 手動起手
  `/speckit-specify`（feature branch `017-audit-retention` 由 specify 建）。

---

## §1 接地盤點（偵察實證精華）

- **reaper bin**（rust-api/server/src/bin/reaper.rs）：`--job <name>` 擴充位在（預設 `token-reap`、
  未知值 exit 1＝B-100 留位）；dry-run／execute 雙姿態；失敗不推成功心跳；JSON log；
  `REAPER_GRACE_DAYS` env fail-default 慣例；心跳 PUT `pushgateway:9091/metrics/job/reaper`
  （grouping key 僅 `job=reaper`）。連線走 `reaper_database_url`（m012 最小權限 role）。
- **purge 執行面**（server/src/handler/audit.rs＋四 facade）：`PurgeTable` 四表封閉白名單
  （operationLog／accessLog／loginAttempt／sessionEvent）；`PURGE_MIN_DAYS=30` 硬底；四表各有
  `purge_before(conn, days)`（`pub(crate)`、txn-scoped 泛型；op-log 版含 `operation <> 'PURGE'`
  固定豁免）；手動端點走 `mutate_in_txn`{DELETE＋PURGE 自記}。★四表**無** count facade（dry-run
  計數屬新增）。
- **schema**：四表皆 `created_at timestamptz NOT NULL`＋created_at btree 索引（cutoff 走索引）；
  `sys_operation_log.created_by` **nullable、無 FK**（archetype B；J2 的 created_by NOT NULL
  構造保證屬 access_log 專屬）；`AuditEvent.operator` 為 `Option`——「無人類操作者」表示法現成。
- **m012 role**：reaper 現僅 `USAGE ON SCHEMA public`＋`SELECT, DELETE ON sys_token`。
- **告警④**（rules.yml obs016-audit-capacity）：四表 `n_live_tup > 1,000,000`、規則內可調——
  B-016 容量監控已落、本刀後退為 backstop。
- **ADR 0075**（B-067 by-design 收單）：「不新增任何自動刪除；reaper 刪除範圍明確不含
  session_event」＋預留「未來 retention 政策刀再議自動化、屆時本 ADR 為現行準據」——本刀
  即該預留時刻、**須 supersede**。
- **憲法島 J3**（v1.10.0 入憲、反轉＝MAJOR）：稽核資料**唯一**刪除路徑＝表白名單×天數水平線；
  **每次 purge MUST 同交易自落操作稽核**（含刪除筆數、**0 列照落**）；op-log 源固定豁免 PURGE
  列（後設證據永久保留）；「拆自記」＝MAJOR。★射程無「管理端」限定＝涵蓋自動刪除。

## §2 拍板記錄

- **Q1 設定存放**（user 親決）：**env 四鍵、無 UI**（最小閉環）。落選＝system_settings 存放
  （reaper 跨面讀 settings＋seed migration、中型）／專屬 admin UI（超出閉環必要範圍）。
- **Q2 稽核軌跡**（user 親決、經重拍）：**遵憲自記**——execute 每表單交易 {水平線 DELETE＋
  PURGE 自記}；自記列 `operator=None`→`created_by NULL`（系統身分、機制現成）＋payload
  `{table, before_days, deleted_count, job:"audit-retention"}`（自動標識、稽核中心可區分人／
  系統）；0 列照落（J3 MUST）；dry-run 不自記（零變動姿態）。
  - ★重拍紀錄：原拍「不自記、純觀測軌跡」——批判複審發現**違憲**（J3「每次 purge MUST 同交易
    自記」＋「拆自記＝MAJOR」）且原選項高估自記累積代價（實際日 4 筆／年約 1460 筆
    ≈0.5MB＝可忽略）。修憲路線（MAJOR bump）成本效益不成比例、落選。
  - 觀測軌跡照舊**雙軌**：JSON log（逐表 deleted／retention_days／mode）＋pushgateway 心跳。
- **預設保留天數**（user 親決）：四表統一 fail-default **90 天**（env 可個別調）。
- **批判複審 4 調整**（user 全收）：①告警補**⑥＋⑥b 成對**（鏡像⑤／⑤b）；②env 下限語意＝
  **前置全拒**；③pushgateway **分組＋一次性清舊組遷移**為硬約束；④ADR 合 1 筆。

## §3 設計

### 3.1 元件

1. **facade**：四表 `purge_before` 由 `pub(crate)` 放寬 `pub`（reaper bin 跨 crate；比照 012
   sys_user helper 先例）＋新增四表 `count_before(conn, days)`（dry-run 計數、走 created_at
   索引）。自記寫入複用既有 AuditEvent 機制（txn 形、可自 bin 呼叫之 pub 面——實作形留 plan）。
2. **reaper bin `--job audit-retention`**：job 分派表（token-reap｜audit-retention）；
   dry-run＝逐表 count＋log＋心跳（不自記）；execute＝逐表單交易 {DELETE＋自記}＋log＋心跳。
   任一表失敗→結構化 error＋exit 1＋不推成功心跳（鏡像 token-reap 契約）。
3. **env 四鍵**：`AUDIT_RETENTION_{OPERATION_LOG,ACCESS_LOG,LOGIN_ATTEMPT,SESSION_EVENT}_DAYS`。
   語意三分：缺席→fail-default 90（合法）；畸形→warn＋退 90（沿 `REAPER_GRACE_DAYS` 家族慣例）；
   **在場且 < 30**（`PURGE_MIN_DAYS` 鏡像 handler 拒絕語意、不 clamp）→**前置全拒**：開跑前驗
   四鍵、任一違規→結構化 error＋exit 1＋零刪除＋不推心跳→告警⑥ 於 2 天內轉紅（fail-loud 閉環）。
   ★刻意不對稱：畸形＝無意圖噪音→退預設照跑；明確設低於下限＝人為意圖但違規→系統不猜、
   零動作（「部分表照跑＋報錯」不採——設定錯誤即零動作、行為最可預測）。
4. **migration m013**：`GRANT SELECT, DELETE ON` 四稽核表＋`GRANT INSERT ON sys_operation_log`
   ＋`GRANT USAGE ON SEQUENCE sys_operation_log_id_seq`（自記 INSERT 之 nextval 需）TO reaper；
   down 對稱 REVOKE；重掛 GRANT 註解錨比照 m012（重建任一相關表之 migration 必同場重掛）。
   純 role／GRANT、**零表結構 DDL**。
5. **compose**：dev entrypoint loop 追加第二 job（`reaper --execute; reaper --job
   audit-retention --execute; sleep INTERVAL`）；base 不動；同一 `reaper_database_url` secret。
6. **pushgateway 分組**（硬約束）：兩 job 各自 grouping key——同組先後 PUT 整組替換會互相清掉
   對方心跳。具體 URL 形（`/job/reaper/reaper_job/<job>` vs 獨立 job 名）留 plan、連動核
   prometheus scrape honor_labels。★遷移：改 grouping key 後舊組 `{job="reaper"}` 殘留序列
   （pushgateway 持久卷）execute 時戳凍結→48h 後⑤誤紅——**一次性清舊組**（`DELETE
   /metrics/job/reaper`、RUNBOOK §9 現成命令）列入遷移步驟。
7. **觀測**：新增告警**⑥**（audit-retention 心跳逾時）＋**⑥b**（dry-run 在而 execute 缺席
   ＝誤配）成對鏡像⑤／⑤b；門檻沿 `172800 = 2×86400` 互錨慣例（同一 sidecar loop 同 INTERVAL、
   rules.yml 與 compose 雙邊註解錨）。告警④退為 backstop（retention 失效才紅）。

### 3.2 資料流

sidecar loop → `reaper --job audit-retention --execute` → reaper role 連線 → 前置驗四 env
（任一 <30 → exit 1 零動作）→ 逐表：單交易 {`purge_before(cutoff=now()-days)` DELETE＋PURGE
自記（operator None、payload 含 job 標識）} → 逐表 JSON log → 心跳（自身 grouping key）。

### 3.3 錯誤處理

- env：缺席 90／畸形 warn+90／低於下限前置全拒（§3.1-3）。
- 任一表交易失敗→error＋exit 1＋不推心跳（已完成之前表交易已 commit——逐表獨立交易、
  部分完成＋整體報錯；下一輪 loop 重試冪等）。
- 「刪了沒記／記了沒刪」構造不可達（同交易、J3）。

### 3.4 測試（TDD）

- facade：四表 `count_before` 新測＋`purge_before` 既有測沿用；op-log 豁免（PURGE 列不被刪）
  於 retention 路徑複證。
- env 解析：缺席／畸形／低於下限三分語意逐鍵；前置全拒＝零刪除機器證。
- bin：job 分派（未知值 exit 1 沿用）；dry-run 零變動＋不自記；execute 刪＋自記列在場
  （operator NULL＋payload job 標識）＋0 列照落。
- 權限整合測：reaper role 可 DELETE 四表＋INSERT op-log；不可 UPDATE 四表／不可 INSERT 他表
  （越權打、比照 016 S5 雙打形）。

## §4 憲法對齊（島 J3 逐條）

- 表白名單×天數水平線 ✓（複用 `PurgeTable`＋`purge_before`、構造禁挑列）；下限守門 ✓
  （env <30 前置全拒＝下限守門的自動化對應）；同交易自記 ✓（每表單交易）；0 列照落 ✓；
  PURGE 豁免 ✓（豁免列＝管理證據、增長率＝手動頻率＋自動日 4 筆、年 ~0.5MB 可忽略——
  非洩漏、by-design 永存）。**零 amendment**。

## §5 ADR draft 候選（1 筆、user 審後立）

- **0076（draft）**：稽核 retention 自動化——遵 J3 自記＋reaper 權限擴張（四表 SELECT+DELETE
  ＋op-log INSERT＋sequence USAGE）＋系統操作者表示法（operator None→created_by NULL＋payload
  job 標識）＋env 四鍵三分語意（90／warn+90／<30 前置全拒）＋⑥/⑥b 成對＋pushgateway 分組遷移。
  `supersedes: [0075]`（「不新增任何自動刪除」「reaper 範圍不含 session_event」就此翻案；
  0075 預留條款「retention 刀再議」即本刀）。落選：純觀測軌跡（違憲 J3 拆自記＝MAJOR）／
  修憲限縮 J3（MAJOR 成本不成比例）／system_settings 存設定（Q1 落選）。

## §6 範圍外與註記

- **首跑巨量刪除**：表已累積大量舊資料時單語句 DELETE 屬大交易（鎖／WAL）——v1 沿 016 單語句
  慣例；prod 部署刀前重估批次化（spec 註記、不入本刀）。
- **RUNBOOK 連帶**（收刀清單）：§4 env 表／§8 audit-retention 手動姿態命令形／pushgateway
  清舊組遷移步驟；§9 pushgateway 清組命令射程更新。
- **B-016 收單帳**：本刀收刀時 B-016 刪列（BACKLOG 完成即刪）。
- 零新 UI／零新錯誤碼／零新依賴／零表結構 DDL（僅 m013 GRANT）。
