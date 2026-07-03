# Data Model: 002-schema-baseline（user 定稿凍結）

本檔＝ADR 0021「user 定稿」的凍結憑據：欄序定稿（§3＝閘 2 欄序基準）、變體歸屬（§1＝
審計守門基準）、刻意差異（§2＝閘 1 白名單來源）、seed 定稿（§4）。轉錄自 user 前置
工作坊產物（rev3 workspace tmp/column-order-decisions.md、2026-07-03 逐表拍板）；
機器互驗義務見 research.md R7（fixtures/scratch-columns.txt diff 通過後閘 2 才啟用）。

## 1. 表清單與 archetype 變體歸屬（憲法 §I.6；審計守門基準）

| # | 表 | 變體 | 審計欄要求 |
|---|---|---|---|
| 1 | sys_user | A 業務全六欄 | 六欄全；user_name 活性唯一（partial-uniq WHERE deleted_at IS NULL） |
| 2 | sys_role | A 業務全六欄 | 六欄全；role_code 活性唯一 |
| 3 | sys_menu | A 業務全六欄 | 六欄全；route_name 活性唯一 |
| 4 | system_settings | A 業務全六欄 | 六欄全（PK＝setting_key、總體唯一、免 partial-uniq） |
| 5 | sys_ip_rule | A 業務全六欄 | 六欄全；wbip_cidr 活性唯一 |
| 6 | sys_operation_log | B append-only 日誌 | 僅 created_at NN＋created_by（operator 域欄）；禁 updated_*／deleted_* |
| 7 | sys_access_log | B append-only 日誌 | 同上（created_by NN） |
| 8 | sys_login_attempt | B append-only 日誌 | 同上（created_by 可空） |
| 9 | sys_user_role | C join | 零審計欄、硬刪；複合 PK＋2 FK |
| 10 | sys_token | C 狀態機 | created_at NN＋created_by NN（擁有者）＋status；無 updated_*／deleted_* |
| 11 | sys_casbin_policy_archive | D 治理 | created_at/by（原 grant 快照、可空）＋archived_at NN def now＋archived_by＋archive_reason NN |
| 12 | casbin_rule | D 治理 | adapter 基底 8 欄＋ALTER 治理欄 protected NN def false／created_at NN def now／created_by |

## 2. 三類刻意差異（rev3 終態 → rev4 定稿；閘 1 白名單來源）

1. **欄序全面重排**：模板「id → 審計六欄（created_at/by、updated_at/by、deleted_at/by）→
   status（狀態／型別欄）→ 業務欄」；log 型 append-only 變體「id → created_at →
   狀態欄 → 業務欄」。casbin_rule 基底欄序 adapter 委派、不重排（ADR 0015）。
2. **改名 11 處（rename map 總表；閘 1 映射基準）**：

   | 表 | 舊欄名 → 新欄名 |
   |---|---|
   | sys_user | current_session_id → session_id |
   | sys_role | code → role_code；name → role_name；home → role_home |
   | system_settings | value_type → setting_type |
   | sys_operation_log | operator_id → created_by |
   | sys_access_log | operator_id → created_by；method → http_method；path → http_path |
   | sys_login_attempt | operator_id → created_by |
   | sys_token | user_id → created_by |
   | sys_ip_rule | rule_type → wbip_type；cidr → wbip_cidr；description → wbip_memo |

3. **新增欄 3 處**（皆 text NULL、seed 全空）：sys_user.user_memo／sys_role.role_memo／
   sys_menu.menu_memo。**型別變更 1 處**：sys_ip_rule.wbip_memo varchar→text。
   ——閘 1 白名單恰為此節 3＋4 項（新增 3 欄＋型別 1 處；改名走映射非白名單）。

## 3. 欄序定稿（逐表；閘 2 機器基準——實庫 ordinal_position 逐欄比對本節表格）

型別／可空／預設的全量機器基準＝fixtures/columns.txt（經 §2 rename map）＋m001 本體
（閘 1 驗之）；本節註記欄僅載定稿拍板時點名的要點。

### 3.1 sys_user（17 欄）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | bigint |
| 4 | updated_at | timestamptz |
| 5 | updated_by | bigint |
| 6 | deleted_at | timestamptz |
| 7 | deleted_by | bigint |
| 8 | status | smallint |
| 9 | user_gender | smallint |
| 10 | user_name | varchar NN（活性唯一） |
| 11 | password | varchar NN |
| 12 | nick_name | varchar |
| 13 | session_policy | varchar(20) NN def 'inherit' |
| 14 | session_id | varchar(36)（★改名） |
| 15 | user_phone | varchar |
| 16 | user_email | varchar |
| 17 | user_memo | text NULL（★新增） |

### 3.2 sys_role（13 欄）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | bigint |
| 4 | updated_at | timestamptz |
| 5 | updated_by | bigint |
| 6 | deleted_at | timestamptz |
| 7 | deleted_by | bigint |
| 8 | status | smallint |
| 9 | role_code | ★改名（原 code）；活性唯一 |
| 10 | role_name | ★改名（原 name） |
| 11 | role_memo | text NULL（★新增） |
| 12 | role_home | ★改名（原 home） |
| 13 | role_desc | |

### 3.3 sys_menu（29 欄）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | bigint |
| 4 | updated_at | timestamptz |
| 5 | updated_by | bigint |
| 6 | deleted_at | timestamptz |
| 7 | deleted_by | bigint |
| 8 | status | smallint |
| 9 | "order" | |
| 10 | hide_in_menu | |
| 11 | keep_alive | |
| 12 | constant | |
| 13 | multi_tab | |
| 14 | protected | NN def false |
| 15 | parent_id | |
| 16 | menu_type | |
| 17 | menu_name | |
| 18 | menu_memo | text NULL（★新增） |
| 19 | route_name | 活性唯一 |
| 20 | route_path | |
| 21 | component | |
| 22 | icon | |
| 23 | icon_type | |
| 24 | i18n_key | |
| 25 | href | |
| 26 | active_menu | |
| 27 | fixed_index_in_tab | |
| 28 | query | jsonb |
| 29 | buttons | jsonb |

### 3.4 sys_user_role（2 欄、照 rev3 原樣）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | user_id | 複合 PK；FK→sys_user.id |
| 2 | role_id | 複合 PK；FK→sys_role.id |

### 3.5 system_settings（10 欄）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | setting_key | varchar(64) PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | bigint |
| 4 | updated_at | timestamptz |
| 5 | updated_by | bigint |
| 6 | deleted_at | timestamptz |
| 7 | deleted_by | bigint |
| 8 | setting_type | ★改名（原 value_type） |
| 9 | setting_value | |
| 10 | description | |

### 3.6 sys_operation_log（13 欄；B 變體）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | ★改名（原 operator_id）、可空、原第 8 位搬前 |
| 4 | operation | |
| 5 | entity_table | |
| 6 | entity_id | |
| 7 | payload_before | jsonb |
| 8 | payload_after | jsonb |
| 9 | operator_real_ip | inet |
| 10 | operator_peer_ip | inet |
| 11 | operator_x_forwarded_for | text |
| 12 | operator_ip_confidence | text |
| 13 | trace_id | varchar(64) |

### 3.7 sys_access_log（12 欄；B 變體）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | ★改名（原 operator_id）、NN |
| 4 | http_status | |
| 5 | http_method | ★改名（原 method） |
| 6 | http_path | ★改名（原 path） |
| 7 | real_ip | inet NN |
| 8 | peer_ip | inet |
| 9 | x_forwarded_for | text |
| 10 | ip_confidence | text |
| 11 | region | |
| 12 | trace_id | |

### 3.8 sys_login_attempt（11 欄；B 變體）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | ★改名（原 operator_id）、可空 |
| 4 | success | |
| 5 | attempted_user_name | |
| 6 | real_ip | inet NN |
| 7 | peer_ip | inet |
| 8 | x_forwarded_for | text |
| 9 | ip_confidence | text |
| 10 | region | |
| 11 | trace_id | |

### 3.9 sys_token（9 欄；C 狀態機變體）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | ★改名（原 user_id）、NN＝token 擁有者 |
| 4 | status | |
| 5 | token_hash | 唯一 |
| 6 | rotation_chain | |
| 7 | issued_at | |
| 8 | expires_at | |
| 9 | used_at | |

### 3.10 sys_ip_rule（11 欄）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | timestamptz NN def now() |
| 3 | created_by | bigint |
| 4 | updated_at | timestamptz |
| 5 | updated_by | bigint |
| 6 | deleted_at | timestamptz |
| 7 | deleted_by | bigint |
| 8 | "order" | 搬位 |
| 9 | wbip_type | ★改名（原 rule_type）、NN |
| 10 | wbip_cidr | ★改名（原 cidr）、inet NN、活性唯一 |
| 11 | wbip_memo | ★改名（原 description）、★型別 varchar→text、NULL |

### 3.11 sys_casbin_policy_archive（13 欄；D 變體、時間欄群前置）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1 | id | bigint PK |
| 2 | created_at | 快照：原 policy 建立時間、可空 |
| 3 | created_by | 快照、可空 |
| 4 | archived_at | NN def now()＝此列誕生 |
| 5 | archived_by | |
| 6 | archive_reason | varchar(32) NN |
| 7 | ptype | |
| 8 | v0 | |
| 9 | v1 | |
| 10 | v2 | |
| 11 | v3 | def '' |
| 12 | v4 | def '' |
| 13 | v5 | def '' |

### 3.12 casbin_rule（基底 8 欄委派＋ALTER 3 欄照原序）

| 序 | 欄名 | 註記 |
|---|---|---|
| 1~8 | id／ptype／v0~v5 | sea_orm_adapter::up() 建；含 unique_key_sea_orm_adapter UNIQUE；欄序不重排（ADR 0015） |
| 9 | protected | ALTER；NN def false |
| 10 | created_at | ALTER；NN def now() |
| 11 | created_by | ALTER |

## 4. seed 定稿清單（241 列；閘 2 seed 基準）

| 表 | 列數 | 內容要點 |
|---|---|---|
| sys_user | 3 | 密碼＝argon2id(123456) 執行期生成（隨機 salt、PHC 格式；三列共用同批雜湊）；user_memo 全 NULL |
| sys_role | 3 | role_memo 全 NULL |
| sys_user_role | 3 | 綁定 user↔role（id 由插入序落位） |
| sys_menu | 78 | 按原 id 升冪插入→id 確定性落 1..78；parent 以 route_name 子查詢解析（對具體 id 值零依賴）；menu_memo 全 NULL |
| casbin_rule | 149 | v1 引用 menu id——與 menu 同批定稿連動（ADR 0023） |
| system_settings | 8 | 鍵值型初始設定 |

- **機器基準**＝fixtures/ 的 6 支 seed json（user 定稿的機器形式、m002 生成來源）；
  閘 2 以 natural key 配對、內容欄逐列比對；password 欄驗 PHC 格式規則非位元比對；
  審計時間戳欄不入內容比對。
- 空表（不 seed）：sys_token、三 log 表、sys_casbin_policy_archive、sys_ip_rule。
- sequence 落點：不寫 id 欄、INSERT 序在空表確定性落 1..N、無 setval。
- 冪等形：每條 INSERT 皆 ON CONFLICT DO NOTHING；A 變體表 conflict target＝partial
  unique index（逐字帶 WHERE deleted_at IS NULL）。

## 5. 索引／約束要點（全量機器基準＝fixtures/indexes.txt＋constraints.txt）

- **活性唯一（partial uniq WHERE deleted_at IS NULL）×4**：sys_user.user_name／
  sys_role.role_code／sys_menu.route_name／sys_ip_rule.wbip_cidr（後二者索引「內容」
  跟新欄名走、索引「名」沿 rev3 原名——閘 1 嚴格比對名與定義）。
- sys_token：token_hash 唯一＋partial (created_by) WHERE status='active'＋rotation_chain
  ＋expires_at 索引。
- sys_login_attempt：(real_ip, created_at)＋(attempted_user_name, created_at)＋
  created_at 單欄索引。
- sys_user_role：複合 PK＋2 FK（→sys_user.id／→sys_role.id）。
- casbin_rule：unique_key_sea_orm_adapter UNIQUE（adapter 建）。
- 複合索引／複合主鍵內部欄序＝語意、閘 1 嚴格比對不正規化。

## 6. 憑據鏈（provenance）

column-order-decisions.md（12 表逐表問答、user 拍板、2026-07-03）→ 本檔 §1~§3；
db 重整後 live 逐列轉錄（tmp/extract/json-*.json）→ 本檔 §4＋fixtures；
雙庫互證（VALIDATION-REPORT.md 八軌全綠）→ 採用前提；
ADR 0021（定稿制）／0023（casbin seed 入基線）／0015（casbin 委派）／0013（短編號）。
