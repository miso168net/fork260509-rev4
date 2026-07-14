# Phase 0 Research: 012-audit-admin

格式＝Decision／Rationale／Alternatives。上游來源＝spec.md（含 clarify 2026-07-15 兩題親決）＋brainstorm
012（D1~D5）＋ADR draft 0057~0060＋三路偵察接地（file:line 皆已核實於 2026-07-15）。

## R1 模糊搜尋＝raw-SQL ILIKE 條件注入＋輸入 escape＋pg_trgm GIN 支撐

- **Decision**：登入嘗試 `attempted_user_name` 與存取日誌 `http_path` 的部分比對走 **ILIKE**（大小寫
  不敏感、FR-003），以 SeaORM `Expr::cust_with_values` 注入條件（`... ILIKE $n ESCAPE '\'`）；使用者
  輸入先 escape `%`／`_`／`\` 再包 `%…%`（萬用字元字面化、FR-003）。索引＝m009 GIN
  `gin_trgm_ops` 兩欄（trigram 同時支撐 ILIKE）。
- **Rationale**：全 repo 零 ILIKE 既例（SeaORM `.contains()`＝`LIKE`、大小寫敏感——sys_user.rs:526 等
  六處皆是），不符 FR-003 大小寫不敏感要求；raw-SQL 條件已有房式（`count_recent_failures`
  之 `Statement::from_sql_and_values`、sys_login_attempt.rs:134-165）。escape 缺席＝使用者輸入 `%`
  會注入萬用語意、違反 Edge Case「字面比對」。
- **Alternatives**：`.contains()`（大小寫敏感、駁回）；`LOWER(col) LIKE LOWER($n)`（需另建函數式索引、
  GIN trigram 本就支援 ILIKE，繞路駁回）；全查詢 raw SQL（放棄 SeaORM 分頁房式、複雜度高駁回）。

## R2 讀端分頁＝沿 user.rs 分頁房式＋新到舊排序

- **Decision**：查詢參數型照 `UserListQuery` 房式——**全 `Option<String>`**（含 current/size；L-090 防
  axum Query 空字串 400）＋`wire_page_u64` trim 解析＋`current.max(1)`／`size.clamp(1,100)`＋wire
  1-based→facade 0-based；時間區間參數收 RFC3339 字串、chrono 解析失敗＝未設；枚舉 filter 照
  `wire_enum12` 嚴格值域範式（值域外＝未設）。排序＝`ORDER BY created_at DESC, id DESC`（FR-001
  新到舊＋同刻識別遞減穩定）；total＝SeaORM `paginate().num_items()`。
- **Rationale**：user.rs:69-80／238-240／448-449 為 011 已驗收房式；空字串=未設（FR-002）與畸形寬鬆
  皆有既例（L-089/L-090）。count 直算於 dev 量級成立；上量後 count 優化屬 B-016 容量警示觸發面
  （spec clarify coverage 之 Outstanding 收斂於此、明文延後）。
- **Alternatives**：數字型 Query 欄（空字串 400、L-090 駁回）；keyset 分頁（前端 hook 範式為
  offset 分頁、駁回）；estimate count（不精確、量級未到、駁回）。

## R3 access-log layer＝authed 子 router 內側＋回應完成後 spawn best-effort

- **Decision**：新增 access-log middleware（axum `from_fn_with_state`），掛於 **`enforce_mw` 下游
  （內側）**——即 authed／policy 子 router 上、`.layer(enforce_mw)` 程式碼順序之前——使其僅於
  已認證請求執行且可讀 `Extension<Claims>`（操作者 id）＋`RequestContext`（信任錨四欄＋trace_id）。
  回應完成後取 status、`tokio::spawn` 非同步寫入 `sys_access_log::insert`（新 facade）——失敗僅
  `warn` 結構化告警（fail-open、FR-009）；region 於寫入時呼 `resolve_region`（xdb 守門沿 ADR 0046、
  auth.rs:171-178 同式）。不讀 body／query string（FR-010——記 `uri.path()` 不含 query）。
- **Rationale**：`Claims` 僅存在於 enforce_mw 下游（router.rs:611-655 分流；Public 子 router 構造上
  不經過本 layer＝FR-010 未認證零列的結構保證）；`sys_access_log.created_by` NOT NULL
  （m001:438）與此一致。spawn 後寫＝寫入不佔請求延遲語意（FR-009）；連線中斷缺列＝明文接受。
- **Alternatives**：全域 layer＋判 Claims 有無（Public 請求也進 layer、再靠 if 濾——結構弱於位置保證，
  駁回）；同步 await 寫入（佔請求延遲，駁回）；middleware 內建重試（best-effort 語意不承諾完整性、
  複雜度不值，駁回）。

## R4 purge＝單交易（DELETE＋op-log）＋PURGE 豁免＋下限常數

- **Decision**：`purgeAuditLog` handler 開單一 txn：①白名單驗 table（四表枚舉、值域外→2222
  `biz.audit.invalidTable`）②`before_days ≥ 30`（server 常數 `PURGE_MIN_DAYS`，違反→2222
  `biz.audit.purgeBelowFloor` 攜 `{minDays}` 明細）③執行水平線 DELETE（op-log 表加
  `AND operation <> 'PURGE'` 固定豁免；其餘三表純水平線）④同 txn 落 op-log
  （`AuditOperation::Purge`、entity_table=目標表、payload_after=`{table, before_days, deleted_count}`、
  deleted_count=rows_affected、0 列照落）⑤commit。一次 DELETE 語句（dev 量級）；大表批次刪除
  屬 B-016 容量警示觸發面、明文延後。
- **Rationale**：DELETE＋自記同交易＝「刪了但沒記」與「記了但沒刪」皆構造不可達（對齊 G1 同交易
  精神）；豁免子句＝clarify Q2 親決（ADR 0058 已載）；rows_affected 取得於 txn 內天然可得。
- **Alternatives**：先記後刪兩段（跨 txn 縫隙，駁回）；分批 DELETE loop（量級未到、複雜度先付，
  駁回）；per-table 專屬端點×4（casbin seed×4＋契約 case×4、參數化單端點更簡，駁回）。

## R5 unlock PG-first 翻轉（B-077）＝op-log 先落硬失敗、Redis 後序

- **Decision**：重排 `unlock_login`（throttle.rs:135-187）動作序為——輸入驗證→**op-log insert
  （PG、失敗即 5000 中止、不動 Redis）**→SET marker→DEL lock（Redis 失敗回 5000、op-log 已留
  「嘗試紀錄」、admin 重按再落一列＝明文接受）。同步：重寫動作序 doc（throttle.rs:117-134）、
  調和既有次序測試 `unlock_handler_source_order_set_marker_before_del_lock`（斷言改為
  op-log→SET→DEL 新固定序）、payload 構造不變（僅 `{dimension, userName, target}` 中性欄）。
- **Rationale**：現序（SET→DEL→op-log best-effort、throttle.rs:183-184 失敗僅 warn）＝「解鎖生效但
  零稽核列」可達（B-077 本體）；PG-first 使其構造不可達（FR-016、島 J5 候選）。「多記嘗試」優於
  「生效無記錄」＝spec 設計取捨節明文。
- **Alternatives**：op-log 失敗重試 N 次仍 best-effort（縫隙仍在、只是變窄，駁回）；事後補記
  補償 job（無 job 基建、複雜度高，駁回）；回報 caller 但不擋生效（稽核列仍缺，駁回）。

## R6 idle 冪等（B-093）＝`set_nx_ex` 標記守門、傾向少記

- **Decision**：`run_refresh` idle 分支（auth.rs:575-596）於 `session_event::insert(idle)` 前加
  `redis::set_nx_ex(cache, idle_emitted_key(sid), "1", ttl.refresh_secs)` 守門——`Ok(true)`（首次）才
  insert；`Ok(false)`（已標記）與 `Err`（標記故障）皆跳過 insert（傾向少記、FR-017）；idle 拒絕
  回應（8888）不受影響。key builder `session:idle-emitted:{sid}` 集中於 redis/mod.rs（比照 :37-77
  既有 builder 群）；TTL＝refresh_secs（對齊 last_activity TTL 慣例、標記存活覆蓋鏈壽命）。
- **Rationale**：idle 分支本身以 redis 讀值為前提（auth.rs:576）、故守門與判定同可用性域；
  `set_nx_ex` 既有原語（redis/mod.rs:197-213、captcha used 同式）。「同 session 恰一列」以 sid 為鍵
  天然對齊 session_event 語意。
- **Alternatives**：DB 查重（每 idle 拒絕多一次 SELECT、且 append-only 表查重窗口語意複雜，駁回）；
  Err→照寫（違 FR-017 傾向少記，駁回）；標記 TTL=idle 門檻（短於鏈壽命、鏈晚期重複觸發再落列，駁回）。

## R7 人員過濾解析（clarify Q1）＝帳號名→識別集合、id 優先

- **Decision**：三個 id 型人員 filter（op-log／access-log `created_by`、session_event `user_id`）各收
  `operatorId`／`userId`（識別等值）**或** `operatorName`／`userName`（帳號名等值解析）：帳號名走
  `SELECT id FROM sys_user WHERE user_name = $1`（**不加 deleted 濾**——含已軟刪同名全部、稽核鏈
  不斷）解析為識別集合→`IN` 條件；零命中→空結果（非錯誤）；兩者同時傳→識別優先、忽略帳號名
  （寬鬆、零新拒因）。
- **Rationale**：clarify Q1 親決 B 案原文落地；帳號名等值（非模糊）＝解析語意封閉、與登入嘗試 tab
  的 trigram 模糊分工明確（那邊是表內文字欄、這邊是跨表解析）。
- **Alternatives**：（clarify 已裁）id only／name only 皆駁回；name 模糊解析（IN 集合爆炸、駁回）。

## R8 打碼單點＝讀端 DTO 構造處統一 mask fn

- **Decision**：`mask_pii_payload(Value) -> Value` 單一純函式（落 audit 讀 facade 或 handler 共用
  mod）：深度一層掃 payload JSON 物件之 `user_phone`／`user_email` 鍵（payload_before／after 兩側、
  任何 entity_table 通用）——字串值電話規則（留前 3 後 2、中段固定 `****`；長度 ≤5 全遮
  `****`）、email 規則（local-part 首字元＋`***`、`@domain` 全留；無 `@` 照 local-part 規則）、
  非字串原樣。op-log 列表 DTO 構造時恰此一處呼叫（島 J4 候選）；負向自證＝讀端回應含
  `0912345678`／原 email 即紅＋mask fn 純函式表驅動單元測試（含異常值降級全路徑）。
- **Rationale**：讀端後端遮蔽＝前端不經手原值（D5／FR-004）；純函式單點＝可表驅動窮舉測試、
  未來新增遮蔽鍵改常數即可（ADR 0059 後果節）。
- **Alternatives**：前端打碼（原值上 wire、違 FR-004，駁回）；落庫遮蔽（回溯清洗＋失去救援快照、
  D5 已裁駁回）；逐 entity_table 特化 mask（重複邏輯，駁回）。

## R9 m009 打包＝extension＋GIN×2＋casbin 2 列＋sys_token 孤兒清理

- **Decision**：單支 `m009_audit_admin.rs`（`execute_unprepared` raw SQL、鏡像 m001:544-588／m008
  範式）：①`CREATE EXTENSION IF NOT EXISTS pg_trgm`（repo 首例、冪等）②GIN×2
  （`idx_login_attempt_user_name_trgm ON sys_login_attempt USING gin (attempted_user_name
  gin_trgm_ops)`、`idx_access_log_path_trgm ON sys_access_log USING gin (http_path gin_trgm_ops)`、
  皆 `IF NOT EXISTS`）③casbin 2 列 additive INSERT（`getSessionEvent` GET＋`purgeAuditLog` POST、
  R_SUPER、WHERE NOT EXISTS 冪等；down 對稱 DELETE）④B-089：`DELETE FROM sys_token WHERE
  created_by NOT IN (SELECT id FROM sys_user)`（一次性、81 列殘留）。同 commit：lib.rs 註冊＋
  `tools/schema-gate` `SEED_ADDITIVE_ALLOWLIST` +2 條七元組。
- **Rationale**：零表結構改動（FR-022）；gate2 凍結 fixtures 與 244 不動（新列走 allowlist 容差、
  schema-gate:411-415 既有機制）；sys_token 不在 `SEED_TABLES`（schema-gate:136-137）＝清理不撞閘、
  無需 removal 機制（偵察已證）。extension 需 superuser——compose dev 的 postgres 預設 superuser、
  可行；quickstart 列驗證步驟。
- **Alternatives**：拆多支 migration（同刀原子交付拆散無益，駁回）；改寫 m002 fixtures（違 ADR
  0032／L-109，駁回）；sys_token 清理走手動 SQL（無版本紀錄、駁回——migration 即史）。

## R10 契約面＝registry 58→63＋datetime offset 守門重建（B-091）

- **Decision**：5 條新 route 全數：router.rs `ROUTES` 條目＋contract.rs `verify_*` fn＋registry 條目＋
  `registered_case_keys` 斷言＋總數斷言 58→**63**（覆蓋閘雙射自動校驗、contract.rs:1478-1505）。
  B-091 兌現：wire_schema.rs 重建 datetime offset 斷言——本刀四讀端時間欄（createTime 等）以
  RFC3339 帶 offset 上 wire，斷言涵蓋本刀新欄＋既有已上 wire 時間欄（009 起 createTime／
  updateTime／archivedAt）。
- **Rationale**：coverage gate 機器強制雙射（每 route 必有 case）；B-091 明文「audit 刀或下次
  contract 擴充」觸發＝本刀命中。
- **Alternatives**：無（機制既定、僅擴充）。

## R11 前端＝四分頁＋daterange spike 先行＋軌道親決前置

- **Decision**：`views/manage/audit/index.vue`＝NTabs 四分頁、每分頁 search 卡＋
  `useNaivePaginatedTable` 遠端表（沿 user 頁房式）；`modules/audit-search-*.vue` 依分頁拆＋
  `modules/audit-purge-modal.vue`（天數輸入＋後果說明＋二次確認）；時間區間＝`NDatePicker
  type="datetimerange"`（全 repo 首次——**首個前端執行單元先 spike 驗證** naive-ui 版本相容、
  §10 風險）；service/typings 走 WRAPPER `rev4-audit.ts`（5 fetcher、直接 import request）＋ADAPT
  `rev4-audit.d.ts`（declaration merging、交叉型別不 merge alias）。i18n 四檔同 commit
  （zh-tw／en-us／zh-cn＋app.d.ts Schema）；purge 拒因 `{minDays}` 為 named-object 插值
  （translateBackendMsg 原生支援、免動 `DETAIL_LIST_ITEM_KEY`）。★前置＝MODAL-WIRING 新用途
  (i)＋島 J 入憲 user 親決（plan Constitution Check 三項、前端執行單元前）。
- **Rationale**：011 已驗收全套範式（agent 偵察 file:line 在案）；insert 值為物件（非陣列）時
  translateBackendMsg 直接 named 插值（request/index.ts:34-42）。
- **Alternatives**：四頁分立（選單 seed 僅一項 manage_audit、違 m002 既定，駁回）；自寫日期輸入
  （棄用元件庫、駁回）；spike 後置（風險後爆炸半徑大、駁回）。

## 研究小結：拍板→落點對照

| 來源 | 拍板 | 落點 |
|---|---|---|
| D1（access-log 全做） | R3 layer＋新 facade | middleware＋facade/sys_access_log.rs（新） |
| D2（session_event 上 UI） | R2/R7 | 讀端×4＋m009 seed |
| D3（pg_trgm 本刀） | R1/R9 | m009＋ILIKE 條件 |
| D4（purge 執行面） | R4 | handler＋PURGE 枚舉＋豁免 |
| D5（顯示面打碼） | R8 | mask fn 單點＋負向自證 |
| clarify Q1（人員過濾雙收） | R7 | 解析 helper＋IN 條件 |
| clarify Q2（PURGE 豁免） | R4 | DELETE 豁免子句＋ADR 0058 |
| B-077 | R5 | throttle.rs unlock 翻轉＋T056 調和 |
| B-091 | R10 | wire_schema datetime 斷言 |
| B-093 | R6 | auth.rs idle 守門＋key builder |
| B-089 | R9 | m009 第④步 |

零 NEEDS CLARIFICATION 殘留。
