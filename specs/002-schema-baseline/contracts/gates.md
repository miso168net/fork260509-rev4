# Contract: 驗證閘（002-schema-baseline）

`tools/schema-gate` 的行為契約（python3 標準庫；DB 存取＝docker compose exec -T postgres
psql 唯讀查詢；需 stack 在跑、不進 pre-commit——與 docs-sync 的離線對賬分工＝spec FR-014）。

## 1. 共同語意

- 退出碼：全綠 0；任一差異 1＋stderr 逐項指名（表／欄／索引名／seed natural key）；
  環境不可用（stack 不在、psql 失敗）＝2＋指名原因（區別「驗證失敗」與「無法驗證」）。
- 唯讀：只 SELECT／information_schema／pg_catalog；絕不寫庫。
- 輸出不含機密值（password 欄不列值、只驗格式規則）。

## 2. `schema-gate gate1` — 結構零漂移（ADR 0021 閘 1）

| 面向 | 契約 |
|---|---|
| 左側 | rev4 實庫（compose stack 的 postgres、soybean_admin_rust） |
| 右側 | specs/002-schema-baseline/fixtures/（columns／constraints／indexes；rev3 live 2026-07-03 凍結） |
| 配對 | 按欄名雙向（右缺＝rev4 多、左缺＝rev4 漏）；14 組表×欄改名經 data-model §2 rename map 映射後配對 |
| 正規化 | 表內欄序不敏感（欄序歸閘 2）；`[]`→NULL；型別以 PG 正規形比對 |
| 嚴格面 | 複合索引／複合主鍵內部欄序逐字；索引名沿 rev3 原名逐字 |
| 白名單 | 恰 4 項（data-model §2 節 3）：user_memo／role_memo／menu_memo 新增、wbip_memo varchar→text——白名單外任何差異＝FAIL |
| 範圍 | 只管結構、不管 seed（ADR 0021）；seaql_migrations 框架表除外 |
| 交叉驗證形 | `gate1 --live-rev3`：右側改連 rev3 活庫直比（rev3＝獨立 compose project，連法＝`docker exec rev3-admin-postgres-1 psql -U soybean -d soybean_admin_rust` 唯讀、容器與帳庫名實作時核對）；rev3 不在機→exit 2（無法驗證）而非誤報差異。rev3 在機時驗收用、fixtures stale 偵測 |

## 3. `schema-gate gate2` — 定稿落實（ADR 0021 閘 2）

| 面向 | 契約 |
|---|---|
| 欄序 | 每表實庫 information_schema.ordinal_position 逐欄＝data-model §3 表格（機器解析 markdown；12 表全比、§3.12 為離散列可直比）；欄名比對前剝除雙引號正規化（"order"→order） |
| seed 集合 | 實庫 6 表列集合＝fixtures 的 6 支 seed json：natural key 配對（user_name／role_code／route_name／casbin ptype+v0..v5／setting_key／user_role 複合鍵）、多列 0 缺列 0 |
| seed 內容 | 內容欄逐列比對；排除：審計時間戳欄（執行期 now()）、password 欄改驗規則（`$argon2id$` 前綴 PHC 格式）、updated_by 與 sys_user.session_id（live 擷取側工作坊編修／登入殘影、定稿 m002 不寫此二欄——fixtures 內 scratch／live 雙 dump 機器 diff 定錨）；jsonb 欄正規化後比（`[]`≡NULL）；id 族不入比對——id 排除、sys_menu.parent_id 以 route_name 解析、sys_user_role 複合鍵解析為 user_name×role_code（§5 還原法 down→up 使 id 前移、直比必假紅） |
| 前置 | data-model §3 轉錄互驗（research R7）通過後本閘才有效——互驗＝fixtures/scratch-columns.txt vs data-model §3 機器 diff |

## 4. `schema-gate audit` — 審計欄建表守門（憲法 §I.6；活書 §8 義務落地）

- 變體歸屬矩陣來源＝`docs/ops/reference-src/archetype-map.json`（002 初始內容＝
  data-model §1 轉錄、本刀兩者一致；後續刀新表隨建表登記——與 docs-sync generate 的
  reference/schema 歸屬欄同源、單一事實家）。逐表驗：
  - A：六審計欄全在、型別對（*_at timestamptz、created_at NN def now、*_by bigint 可空）；
    soft-delete 表另驗 partial-uniq WHERE deleted_at IS NULL 在場（PK 總體唯一者除外）。
  - B：created_at NN 在場；**updated_*／deleted_* 出現＝FAIL**（不可竄改性）。
  - C：sys_user_role 零審計欄（出現任一審計欄＝FAIL）；sys_token 恰 created_at＋
    created_by＋status、無 updated_*／deleted_*。
  - D：sys_casbin_policy_archive 驗 archived_at NN／archived_by／archive_reason NN＋
    created_at/by 可空；casbin_rule 驗 ALTER 三治理欄在場且基底 8 欄未被動。
- 表清單以 archetype-map.json 為準（002＝12 表）；實庫多出清單外業務表＝FAIL
  （防未登記建表）。
- 本命令供後續每刀重跑（新表入庫前先補 data-model §1 歸屬、否則此閘攔）。

## 5. 負面驗證形（驗收用、注入必還原）

- gate1 負面：實庫暫 ALTER TABLE ADD COLUMN 計畫外欄 → gate1 FAIL 指名 → DROP 還原 → 綠。
- gate2 負面：暫 DELETE 一列 seed（natural key 指定）→ gate2 FAIL 指名該鍵 → 還原＝
  容器內 migration CLI `down`（回捲 m002）→`up`（重放 m002 補回）、或依 fixtures json
  單列 INSERT。**注意**：重跑 migrate 服務＝no-op（seaql_migrations 已記錄 m002、框架
  跳過、不會補插）——不可作為還原法。還原後重跑綠。
- audit 負面：主庫暫建一張未登記 probe 表（如 `t_audit_probe`）→ audit FAIL（清單外
  業務表）→ DROP 還原 → 綠。所驗＝清單守門面；欄級檢查由 12 表正面矩陣覆蓋、
  不另做破壞性欄注入。
