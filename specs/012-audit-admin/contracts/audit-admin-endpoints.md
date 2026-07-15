# Contract: 012-audit-admin 5 端點（4 GET 讀端＋1 purge 寫端）

**Branch**: `012-audit-admin` | **Date**: 2026-07-15 | **Plan**: [plan.md](../plan.md)

本檔為本刀 wire 契約封閉全集。envelope `{data, code, msg}` 凍結；business error 走 HTTP 200＋
`2222`＋msg=i18n key；權限拒絕走既有 `5003`→403；**零新錯誤碼**（FR-024）。分頁形＝
`PageRes<T>`＝`{current, size, total, records}`。時間欄一律 RFC3339 帶時區偏移（B-091 斷言重建
於 wire_schema）。id 類欄位 i64→JSON number（2^53 fail-loud 守衛沿房式）。

★契約紀律：每條 route 必有 contract case（registry 58→**63**、覆蓋閘雙向雙射
contract.rs:1478-1505）；case_key 命名照 router 既例 kebab-case（下表暫名、實作對齊）。

## seed 增量（m009；三支 GET 政策 m002 已埋）

| # | ptype | v0 | v1 | v2 | 來源 |
|---|---|---|---|---|---|
| — | p | R_SUPER | `/systemManage/getOperationLog` | GET | m002:344（已埋） |
| — | p | R_SUPER | `/systemManage/getAccessLog` | GET | m002:345（已埋） |
| — | p | R_SUPER | `/systemManage/getLoginAttempt` | GET | m002:346（已埋） |
| 1 | p | R_SUPER | `/systemManage/getSessionEvent` | GET | ★m009 |
| 2 | p | R_SUPER | `/systemManage/purgeAuditLog` | POST | ★m009 |

m009 之 2 列同 commit 登記 `SEED_ADDITIVE_ALLOWLIST`（七元組）；fixtures／244 不動；
零按鈕碼 seed（整頁 menu 政策供裝、FR-025）。

## 型別（全新形、ADAPT 軌道 `rev4-audit.d.ts` declaration merging 併 `Api.SystemManage`）

- 搜尋參數共通形＝`CommonType.RecordNullable<專屬欄 & CommonSearchParams>`（沿凍結
  `UserSearchParams` 範式）；共通專屬欄：`timeFrom?`／`timeTo?`（RFC3339 字串、閉開區間）。
- 各源專屬（皆 camelCase wire）：
  - `OperationLogSearchParams`：`entityTable?`、`operation?`、`operatorId?`、`operatorName?`
  - `AccessLogSearchParams`：`httpMethod?`、`httpStatus?`、`operatorId?`、`operatorName?`、`httpPath?`（模糊）
  - `LoginAttemptSearchParams`：`success?`（'true'/'false' 字串收斂）、`realIp?`（精確）、`userName?`（模糊）
  - `SessionEventSearchParams`：`userId?`、`userName?`（等值解析）、`eventType?`、`reason?`
- 列型（逐欄構造、data-model §1 欄集 camelCase 鏡像；重點欄）：
  - `OperationLog`：`id`、`createTime`、`operatorId`、`operatorName`（可 null）、`operation`、
    `entityTable`、`entityId`（可 null）、`payloadBefore`／`payloadAfter`（★打碼後 JSON、可 null）、
    `operatorRealIp`…四欄、`traceId`
  - `AccessLog`：`id`、`createTime`、`operatorId`、`operatorName`、`httpMethod`、`httpPath`、
    `httpStatus`、`realIp`…四欄、`region`、`traceId`
  - `LoginAttempt`：`id`、`createTime`、`attemptedUserName`、`success`、`realIp`…四欄、`region`、`traceId`
  - `SessionEvent`：`id`、`createTime`、`userId`、`userName`（可 null）、`sid`、`eventType`、`reason`、
    `operatorId`（可 null）、`operatorName`（可 null）、`sourceIp`（既有單欄字串形照回）
- 人員過濾語意（clarify Q1）：`*Id` 與 `*Name` 擇一；同傳→Id 優先；Name 解析含已軟刪同名全部；
  零命中→空頁。

## 端點表

### US1 讀端四支（P1）

| # | path | method | 政策角色〔seed〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 1 | `/systemManage/getOperationLog` | GET | R_SUPER〔m002 已埋〕 | `OperationLogSearchParams` | `PageRes<OperationLog>`（payload 經 mask 單點；**回應 0% 含電話/email 原值**、負向自證）｜讀端零拒因（參數寬鬆） |
| 2 | `/systemManage/getAccessLog` | GET | R_SUPER〔m002 已埋〕 | `AccessLogSearchParams` | `PageRes<AccessLog>`（httpPath ILIKE 模糊＋trigram；萬用字元字面化） |
| 3 | `/systemManage/getLoginAttempt` | GET | R_SUPER〔m002 已埋〕 | `LoginAttemptSearchParams` | `PageRes<LoginAttempt>`（userName ILIKE 模糊；節流短路零列＝表語意、UI 明示 FR-021） |
| 4 | `/systemManage/getSessionEvent` | GET | R_SUPER〔★m009〕 | `SessionEventSearchParams` | `PageRes<SessionEvent>`（eventType/reason 封閉集等值） |

**共通語意**：`created_at DESC, id DESC` 新到舊穩定排序；`current`≥1／`size` clamp 1..100；
空字串/畸形參數＝未設；時間顛倒＝空結果；讀端 handler 零寫入（FR-007）。

### US3 purge（P3）

| # | path | method | 政策角色〔seed〕 | req | res data｜拒因 |
|---|---|---|---|---|---|
| 5 | `/systemManage/purgeAuditLog` | POST | R_SUPER〔★m009〕 | `{table, beforeDays}`（table∈`operationLog`/`accessLog`/`loginAttempt`/`sessionEvent` 封閉枚舉） | `{deletedCount}`｜`2222 biz.audit.invalidTable`／`2222 biz.audit.purgeBelowFloor`＋`{minDays:30}` 明細 |

**守門固定序**：①table 白名單 → ②beforeDays ≥ 30 → txn{③水平線 DELETE（op-log 加
`operation <> 'PURGE'` 豁免）→ ④PURGE 自記（payload={table, before_days, deleted_count}、
0 列照落）} → commit。

### 存取軌跡記錄（US2、非端點——layer 契約）

- 觸發＝一切通過 enforce_mw 的請求（Authed＋Policy 路由全集、含本刀讀端自身；Public 構造上
  不觸發）；每請求恰一列；response 完成後非同步寫、fail-open（寫失敗僅 warn、業務回應零影響）。
- 落列欄：method／path（**不含 query**）／status／Claims.uid→created_by／信任錨四欄／region
  （best-effort）／trace_id。

## 拒因鍵（一因一鍵、三語＋Schema 同 commit）

| 鍵 | 觸發 | 插值 |
|---|---|---|
| `backend.biz.audit.invalidTable` | purge 資料源不在白名單 | — |
| `backend.biz.audit.purgeBelowFloor` | 清理天數低於下限 | `{minDays}` |

（後端發出 `biz.audit.*`、前端 translateBackendMsg 統一 prepend `backend.`；named-object 明細
原生插值、免動 `DETAIL_LIST_ITEM_KEY`。）

## 前端 fetcher 對帳（WRAPPER `rev4-audit.ts`、直接 import request、不進 barrel）

| fetcher | 端點 | method |
|---|---|---|
| `fetchGetOperationLog` | `/systemManage/getOperationLog` | get（params） |
| `fetchGetAccessLog` | `/systemManage/getAccessLog` | get（params） |
| `fetchGetLoginAttempt` | `/systemManage/getLoginAttempt` | get（params） |
| `fetchGetSessionEvent` | `/systemManage/getSessionEvent` | get（params） |
| `fetchPurgeAuditLog` | `/systemManage/purgeAuditLog` | post（data） |

i18n 隨建頁：`route.manage_audit`＋`page.manage.audit.*`＋`backend.biz.audit.*`（zh-tw／en-us／
zh-cn＋`App.I18n.Schema` 四檔同 commit、圈界 `rev4-inline I18N-WIRING(ii)/(iii)`）。
