# 012-audit-admin — 稽核中心（audit 管理面）brainstorm

> 2026-07-14；方法＝三支並行偵察（後端基建／前端基線／治理承襲）＋五題澄清（user 逐題親決）
> ＋設計 A/B/C 三段逐段確認。下一步＝手動 `/speckit-specify`（input＝本檔）。
> 家族序 role→menu→user→**audit**→ip-rule 第四刀；母體拍板＝ADR 0011（rev3）。

## 0. 接地盤點（事實地基、逐 file:line）

### 0.1 資料源四表現況（schema 真源＝docs/generated/reference/schema.md；entity 逐欄一致無漂移）

| 表 | archetype | 欄數 | 寫入端現況 | 查詢面現況 | 既有索引（時間類） |
|---|---|---|---|---|---|
| sys_operation_log | B append-only | 13 | 七子系統經 `mutate_in_txn`／`write_in_txn`（sys_user/sys_role/sys_menu/sys_ip_rule/system_settings/casbin archive/throttle unlock） | **零**（僅 test by-trace） | created_at；(created_by,created_at) |
| sys_access_log | B append-only | 12 | ★**零寫入端**（entity＋schema＋casbin seed 齊備、無 facade 無 middleware） | 零 | created_at；(created_by,created_at) |
| sys_login_attempt | B append-only | 11 | `record_attempt`（server/src/handler/auth.rs:464）；節流短路 1000 零列＝島 E3 by-design | 僅節流計數聚合（count_recent_failures／_by_ip）、無列表 | created_at；(real_ip,created_at)；(attempted_user_name,created_at) |
| session_event | B append-only | 8 | auth.rs ×4（kicked/idle/reuse/logout）＋facade/sys_user.rs record_session_events（revoked/kicked；reason∈user_disabled/user_deleted/admin_kick/password_reset） | **零** | (user_id,created_at) |

- 全四表無 FK、無 deleted_at（變體 B：只 created_at NN、不可竄改、MUST NOT 加 updated_*/deleted_*，憲法 §I.6）。
- session_event.source_ip＝varchar(45)（非 inet 雙欄形，entity/src/session_event.rs:5）；打 wire 時照現形回傳。
- 旁列：sys_token（archetype C 狀態機、非稽核源）81 筆 created_by 孤兒列（009/010 測試帳號硬刪殘留；
  gate2 只驗欄形變體矩陣、不驗參照存在性故不擋閘）＝B-089 順帶標的。

### 0.2 授權與選單殼（m002 預埋、「有殼無 API 無頁」）

- `manage_audit` 選單 seed：migration/src/m002_baseline_seeds.rs:195（route_path=/manage/audit、
  component=view.manage_audit、i18n_key=route.manage_audit、icon mdi:clipboard-text-search-outline、order 6）。
- casbin p 列已 seed 三支 GET（m002:344-346）：`/systemManage/getOperationLog`／`getAccessLog`／
  `getLoginAttempt`（皆 R_SUPER）；menu 政策 m002:347＋g 綁定 m002:533。
- `server/src/router.rs` ROUTES 零 audit 端點（逐條驗證）；route locale 三語缺（B-061）→選單顯 raw key、點擊 404。
- session_event 讀端與 purge 端點**無 seed**——本刀新 migration 補。

### 0.3 op-log 寫入基建（讀端要消費的形狀）

- 原子接縫：`mutate_in_txn`（server/src/model/audit.rs:94-107）業務寫＋op-log 同 txn。
- `AuditOperation` 枚舉（audit.rs:31-42）＝UPDATE/UNLOCK/INSERT/SOFT_DELETE/RESTORE/KICK/RESET_PASSWORD；
  `entity_table` 欄＝天然資料源分類鍵。
- 四支寫 helper（facade/sys_operation_log.rs:32,42＋facade/session_event.rs:15＋facade/sys_login_attempt.rs:40）
  現皆 `pub`；NOTES minor「pub→pub(crate) 收斂」本刀順手兌現。
- payload 白名單構造：sys_user `AuditSerialize`（facade/sys_user.rs:122-144）逐欄手構、
  **password（argon2 PHC）與 session_id 永不入列**（負向自證 t009_* 斷言、島 I5）；
  但 user_phone/user_email/nick_name/user_memo **在列**（B-044 的實況：011 起既成落庫）。
- kick/reset payload＝恰 {id, user_name} 二中性欄（facade/sys_user.rs:161-170）。

### 0.4 前端現況與可循範式

- soybean example 基線零 monitor/log 頁；可循範式＝manage/user（useNaivePaginatedTable＋NDataTable remote，
  views/manage/user/index.vue:53-56,384-396）＋policy-archive-search（唯讀多濾條輕量搜尋）。
- ADAPT/WRAPPER 慣例：新 service 檔直接 `import { request } from '../request'` 不進 barrel
  （service/api/rev4-user-admin.ts:1-6）；typings declaration merging 併 Api.SystemManage、凍結檔零改動。
- dynamic 選單：component=view.manage_audit 由 elegant transform 解析、**無對應 view 檔即 throw**
  （router/elegant/transform.ts:61-62）→建頁後 codegen 四產物（imports/routes/transform/elegant-router.d.ts）自動生成。
- route locale 三檔位置：zh-tw.ts:358 附近 manage 家族區塊（zh-cn/en-us 對齊）。
- ★全 repo 零 `NDatePicker`/daterange 用例＝時間區間選擇器 net-new（風險點）。

### 0.5 治理承襲（rev3→rev4）與必守條款

- **ADR 0011（rev3、accepted）＝母體**：稽核三表補查詢讀端＋僅超管 UI、read-only reporting、刻意殿後；
  trigram＝B-039、retention＝B-016 的切分權威。本刀＝兌現＋增補（四源）。
- 必守：§I.6 變體 B（append-only 不可竄改）；島 E3 恰一列（登入終局才落列、短路零列）；G1/I2 op-log 同交易；
  I5 payload 不洩（密碼/會話識別、反轉＝MAJOR）；E1/F3 稽核寫故障 fail-OPEN；F4 位址取信任錨；
  §III.2 MODAL-WIRING(e)（route locale 隨建頁、不得獨立新增）。
- 跨刀承諾彙總（觸發命中本刀）：B-016（政策續留）／B-039／B-044／B-061 audit 項／B-077／B-088／B-089／B-091／B-093。

## 拍板紀錄（2026-07-14、user 逐題親決；設計 A/B/C 三段逐段 OK）

| # | 題 | 拍板 | 歸檔 |
|---|---|---|---|
| D1 | sys_access_log 有表無寫入端怎麼辦 | **全做**：寫入 middleware＋讀端＋UI（選項 a；不取空表上架/整包延後） | ADR 0060 |
| D2 | session_event 上不上 UI | **上**：第四資料源＋新 casbin seed（不守三表打住） | ADR 0057 |
| D3 | 查詢能力 v1 | **模糊搜尋＋pg_trgm 本刀 schema 期落地**（照 B-039 rev3 已驗證結論） | ADR 0057 |
| D4 | purge | **執行面本刀**（手動、僅超管、時間水平線唯一形狀、下限守門、自落 op-log）；保留天數政策不拍、B-016 續留 | ADR 0058 |
| D5 | op-log payload PII | **顯示面打碼**（讀端後端遮蔽電話/email）；落庫照白名單現況定調（收 B-044） | ADR 0059 |

## §1 總覽

一句話：**「稽核中心」一頁四 tab（操作日誌／存取日誌／登入嘗試／會話事件）、僅超管、read-only
reporting**；唯二寫面＝access-log 寫入 middleware（D1）與 purge 水平線清舊（D4）。兌現 ADR 0011
並增補為四源。後端＝四支 GET 讀端＋一支 purge POST＋一個 axum 寫入 layer；schema 期＝pg_trgm＋
GIN 索引＋casbin seed 兩列＋B-089 清理（零表結構改動）；前端＝MODAL-WIRING(e) 建頁全量走完
（兌現 B-061 audit 項）。家族範式照 011：facade→handler→router、ADAPT/WRAPPER、TDD＋雙審查。

## §2 讀端四支 GET

- 端點名照 m002 seed 既定：`getOperationLog`／`getAccessLog`／`getLoginAttempt`＋新 `getSessionEvent`。
- 分頁形狀對齊 getUserList 範式（current/size/total/records；CommonSearchParams）。
- filter 矩陣（全表共通＝時間區間〔created_at 閉開區間〕＋分頁）：

| tab | 專屬精確 filter | 模糊（trigram） |
|---|---|---|
| 操作日誌 | entity_table、operation、created_by（操作者） | —（payload jsonb 搜尋不做、YAGNI） |
| 存取日誌 | http_method、http_status、created_by | http_path |
| 登入嘗試 | success、real_ip（inet 精確） | attempted_user_name |
| 會話事件 | user_id、event_type、reason | — |

- facade 各表新增 read-only list 函式（唯讀、無寫面）；四支寫 helper 順手 pub→pub(crate)。
- ★PII 打碼在**後端讀端**做（遮蔽後才上 wire、前端不經手原值）：key-based 掃 payload JSON 的
  `user_phone`／`user_email` 鍵（含 payload_before/payload_after 兩側；對任何 entity_table 通用）。
  渲染前後對照：`0912345678 → 091****78`；`andy@example.com → a***@example.com`
  （規則：電話留前 3 後 2、中段固定 `****` 不保留原長度〔不洩長度資訊〕；email local-part
  留首字元＋固定 `***`、domain 全留）。
  負向自證：讀端回應含電話/email 原值即紅。

## §3 access-log 寫入 middleware（D1）

- axum layer 掛 protected 路由群：已認證請求每 request 落一列（created_by NOT NULL 天然排除
  未認證流量；登入行為歸 sys_login_attempt 管、不重疊）。
- 欄位：http_method／http_path／http_status＋IP 信任錨四欄（real/peer/xff/confidence、島 F4）＋
  region（GeoIP best-effort、沿 ADR 0046）＋trace_id；response 完成後寫。
- **best-effort fail-open**：寫失敗只 warn、絕不擋業務請求（對齊島 E1/F3 精神；入憲候選 J2）。
- ★不記 request body／query string（零 PII 入列、免遮蔽問題）；audit 自家讀端請求照記（一致性、無豁免名單）。

## §4 purge 執行面（D4）

- 一支 `POST /systemManage/purgeAuditLog`（casbin seed 一列、R_SUPER）；參數 `{table, beforeDays}`、
  table 限四稽核表枚舉白名單。
- 守門：**只能整段時間水平線刪**（`DELETE WHERE created_at < now() - beforeDays`，構造上不可能挑列
  ＝防選擇性滅證）；beforeDays 下限 **30 天** server 常數寫死（防手滑清近期；政策天數 B-016 拍板後才動）。
- purge 動作自落 op-log：`AuditOperation` 新增 `Purge`（"PURGE"）、payload＝{table, before_days, deleted_count}
  ——刪過什麼範圍永遠有案可查（水平線語意下新列 created_at=now 恆不落入自身刪除範圍）。
- UI：每 tab 一顆清理鈕→modal 輸入天數＋二次確認；拒因（下限違反等）走 backend.biz.audit.* 結構化明細三語。

## §5 schema 期 migration（一支打包；編號＝migration 目錄下一號，現況為 m009）

1. `CREATE EXTENSION IF NOT EXISTS pg_trgm`＋GIN trigram 索引兩欄：
   `sys_login_attempt.attempted_user_name`、`sys_access_log.http_path`（D3；模糊搜尋主戰場）。
2. casbin seed 補兩列：`getSessionEvent` GET＋`purgeAuditLog` POST（R_SUPER；走 ADR 0032 新增放寬軌道；
   gate2 期望值同步）。
3. B-089 一次性清理：`DELETE FROM sys_token WHERE created_by NOT IN (SELECT id FROM sys_user)`（81 列孤兒）。
4. ★零表結構改動：無新表、無新欄、無型變。

## §6 前端接線（MODAL-WIRING(e) 全量）

- `views/manage/audit/index.vue`＝一頁四 tab（NTabs），每 tab＝search 卡＋NDataTable remote 分頁
  （抄 manage/user＋policy-archive-search 範式）；`modules/` 下 search 元件依 tab 拆分。
- 時間區間＝net-new `NDatePicker type="daterange"`（全 repo 首次引入、§10 風險列管）。
- `service/api/rev4-audit.ts`（WRAPPER、直接 import request、不進 barrel）＋
  `typings/api/rev4-audit.d.ts`（ADAPT、declaration merging 併 Api.SystemManage）；凍結檔零改動。
- locale 三語隨建頁補：`route.manage_audit`＋`page.manage.audit` 區塊＋`backend.biz.audit.*` 拒因鍵
  （i18n Schema 同 commit）；elegant-router 四產物 codegen 自動生成、不手改。
- 無按鈕碼 seed：整頁 menu 政策已限超管、purge 鈕不另設 button 碼（m002 對 audit 零 button 列；
  將來下放唯讀權限再議）。

## §7 housekeeping 折入（工程拍、回報備查）

- **B-077** unlock 零稽核列：動作序翻轉 **PG-first**——op-log 先落（PG）、成功才動 Redis
  （SET marker→DEL lock）；Redis 失敗回 5000、admin 重按（多一列「嘗試紀錄」可接受；對齊島 I2
  PG-first 精神；入憲候選 J5）。消滅「動作生效但零稽核列」。
- **B-093** idle 稽核冪等：首次 idle 才落列（sid 級 Redis SETNX 標記、重複 idle 跳過 insert）；
  UI 會話事件 tab 直接可驗治理前後。
- **B-091** datetime offset 守門：四表讀端回 createTime＝contract 擴充命中→本刀兌現守門義務
  （重建 offset 斷言）。
- **B-088** notRestorable dead-key＋四文件漂移：errata 紀律四處一併、隨刀 housekeeping。
- **B-089**：已折入 §5 migration。

## §8 治理

- 憲法新島 J（audit 域）候選、v1.10.0（措辭 spec/plan 期定稿）：
  J1 稽核讀端 read-only＋僅超管／J2 access-log 寫入 fail-open 絕不擋業務請求／
  J3 purge 唯一形狀＝時間水平線＋自落 op-log（構造上禁選擇列刪）／
  J4 PII 顯示面打碼單點（讀端後端遮蔽、前端不經手原值）／J5 unlock 稽核先於生效（PG-first）。
- ADR draft 四筆隨本檔同 commit：0057（四源讀端＋查詢能力；增補 0011 非翻案）／0058（purge 執行面）／
  0059（PII 落庫白名單＋顯示面打碼、收 B-044）／0060（access-log 寫入端啟用）。accepted 時機＝spec 定稿。
- BACKLOG 簿記（收刀時）：兌現刪列 B-039／B-044／B-061 audit 項（殘 ip-rule）／B-077／B-088／B-089／
  B-091／B-093；B-016 續留（觸發不變）。
- 零新錯誤碼（沿 2222 biz／5000）；零新依賴（pg_trgm＝PG contrib）。

## §9 測試與驗收

- TDD 負向自證：①打碼（讀端回應含電話/email 原值即紅）②purge 水平線（構造上無法挑列、下限守門拒因）
  ③middleware fail-open（access-log 寫故障不擋業務請求）④idle 冪等（重複 idle 恰一列）
  ⑤unlock PG-first（op-log 失敗則 Redis 不動）。
- 契約 registry 擴充雙射（四支 GET＋purge）；casbin seed 新增→gate2 期望值同步；schema-gate audit 照跑。
- CDP 實機（Edge@9229）：S1 四 tab 顯示與分頁、S2 模糊搜尋（部分帳號名/路徑）、S3 打碼渲染
  （091****78）、S4 purge 全流程＋op-log 自記一列、S5 三語零 raw key（route.manage_audit 兌現 B-061）、
  S6 access-log 點頁即落列。
- 慣例照舊：rust 容器內 build/test 全 serial；fork-delta-lint（base-web 動即跑）；typecheck；
  Workflow 編排 TDD＋雙審查（CLAUDE.md §2 範本）。

## §10 風險與備註

- net-new NDatePicker daterange：soybean/naive-ui 版本相容未實測——首個執行單元先 spike 驗證。
- access-log 量級：每已認證請求一列、dev 環境即可觀察成長速率；容量監控與自動化續留 B-016（obs 面不入本刀）。
- purge vs 變體 B「不可竄改」：以 ADR 0058 錨定「水平線 retention 刪除≠竄改」的憲法解釋，
  入憲 J3 時同步收斂措辭。
- session_event 讀端擴 0011 三表→四源：0057 定調為「增補」非翻案（0011 不 supersede）。
- 節流短路 1000 零列＝島 E3 by-design（ADR 0037）：登入嘗試 tab 的資料語意要在 UI 文案/驗收中
  講清楚「短路拒絕不在此表」，防誤判漏記。

## 交棒（SDD）

手動起 `/speckit-specify`（input＝本檔）；spec 期定稿：wire 契約欄名／filter 參數名／打碼規則
邊界（超短電話、無 @ 的異常值）／島 J 措辭／migration 實際編號；US 切法建議：讀端四 tab（P1）→
access-log 寫入（P2）→purge（P3）→housekeeping 折入（P4）→i18n 與 CDP（P5）。
