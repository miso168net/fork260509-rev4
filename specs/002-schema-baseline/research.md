# Research: 002-schema-baseline

Phase 0 產出。所有決策面未知已於刀內 brainstorm（6 題拍板、2026-07-04）與前置工作坊
（user 於 rev3 session 完成、2026-07-03）解決——本檔彙整拍板＋plan 級技術決定；
Technical Context 零 NEEDS CLARIFICATION。拍板全文＝`docs/brainstorms/002-schema-baseline.md`
§0（凍結）；定稿憑據原件＝rev3 workspace tmp/（column-order-decisions.md、
VALIDATION-REPORT.md、m001/m002 原檔、extract/ dump）。

## R1. 依賴與版本（brainstorm 拍板 #6＋自拍備查）

| 元件 | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| argon2 | 0.5.3（workspace.dependencies） | rev3 lock 現值＝crates.io 最新 stable；「lock 現值＝官方最新→沿用」原則（001 tower 前例） | 無（雙查同值、零分歧） |
| sea-orm-cli | 1.1.20（工具、一次性） | 與 sea-orm-migration 1.1.20 同版配對＝codegen 產物與 runtime 型別零世代差；user 拍板 | 純手寫（推翻生成起手案、被否） |
| sea-orm | 1.1.20（001 R1 已釘；本刀首個消費者＝entity） | workspace 版本單一來源；**default-features=false**＋per-crate features（rev3 慣例沿用） | — |
| entity features | macros＋with-chrono＋with-json＋with-ipnetwork | rev3 entity crate 現值＝L-071 解法：chrono backend 供 timestamptz（DateTimeWithTimeZone）、ipnetwork 供 inet、json 供 jsonb | with-time backend：rev3 為 MSRV 刻意避開 time crate、rev4 雖無 MSRV 壓力但沿已驗證形零遷移成本 |
| async-trait | **不另引** | sea-orm-migration prelude 再匯出；tmp 雙庫互證編譯已實證 | 顯式引入 0.1 浮動（rev3 形、違釘版紀律） |
| sea-orm-adapter | vendored 整檔拷入（源＝rev3 workspace 的 `rust-api/sea-orm-adapter/`） | 憲法 §I.5 明文例外（工具性 crate、已驗證）；m001 的 casbin_rule 委派建表依賴它（ADR 0015） | crates.io 版 sea-orm-adapter：與 rev3 已驗證行為非同源、違例外條款本意 |

- **U1 實作補記**：vendored adapter 的 manifest 以 workspace 繼承宣告 async-trait 與
  casbin——workspace.dependencies 補定義 async-trait 0.1.89、casbin 2.20.0
  （default-features=false）；兩者 rev3 lock 現值＝crates.io 最新 stable（雙查同值、
  沿用原則）。上列「不另引」維持成立於 migration 碼面（prelude 再匯出）。

## R2. migration 檔名與 lineage 改寫（plan 級自拍）

- **檔名**＝`m001_baseline_schema.rs`／`m002_baseline_seeds.rs`：ADR 0013 短編號＋語意名；
  DeriveMigrationName 使檔名成為 seaql_migrations 永久記錄名——不帶前代代號（L-049 紀律
  延伸至 DB 記錄）。Alternatives：沿 tmp 原名（帶 rev3 字樣、否）；長時間戳（ADR 0013 已否）。
- **檔頭註解改寫**：lineage 指向 `specs/002-schema-baseline/data-model.md`＋fixtures
  （001 config.rs 引 specs 契約的既有形）；「三類刻意差異」全文歸 data-model §2。
- **防回歸清單**（§I.5 條款、對照 rev3 不帶回）：浮動版本宣告（async-trait "0.1" 形）、
  長編號 migration 檔名、grafana 第七機密線（001 已裁）。
- **DDL／DML 語意零改動**：tmp 產物＝雙庫互證八軌全綠的定稿，內容不重寫、只改上述兩類
  外圍（改寫後以 quickstart A＋閘 1／閘 2 重證）。

## R3. 閘 1 基準與比對配方（brainstorm 拍板 #3＋plan 級細化）

- **基準＝凍結 fixtures**：`tmp/extract/` 全套拷入 `specs/002-schema-baseline/fixtures/`
  （columns／constraints／indexes／sequences／row-counts＋6 表 seed json；檔頭標
  「來源＝rev3 live、擷取 2026-07-03」）。rev3 在機時驗收加跑一次 live 直比交叉驗證。
- **比對配方**（沿 VALIDATION-REPORT 已驗證方法）：rename map 14 組（表×欄）雙向映射；表內欄序
  不敏感（欄序歸閘 2）；複合索引／複合主鍵內部欄序嚴格；刻意差異白名單恰為
  3 memo 欄（新增）＋wbip_memo varchar→text（型別）；`[]`→NULL 正規化；審計時間戳
  「值」不比（結構比對本就不涉值）。
- Alternatives：live rev3 直比（rev3 下線即失效）；九支 migration 重放（要拷 rev3
  migration 碼、工程最大）——皆已於 brainstorm 否決。

## R4. 閘工具形態（plan 級自拍）

- **單支 `tools/schema-gate`**（python3 標準庫；DB 存取走 `docker compose … exec -T
  postgres psql` 唯讀查詢）；子命令 `gate1`／`gate2`／`audit`；全綠 exit 0、任一差異
  exit 1＋逐項指名（表／欄／列 natural key）。
- 不進 pre-commit（需 stack 在；FR-014 分工）；與 docs-sync 分離（後者守離線秒級）。
- 閘 2 欄序基準＝data-model §3 表格（機器解析 markdown 表）；seed 基準＝fixtures 的
  6 支 json（= m002 生成來源、user 定稿機器形式）；argon2 欄驗 PHC 格式規則
  （`$argon2id$` 前綴）非位元比對。
- 審計守門（audit 子命令）＝依 data-model §1 變體歸屬矩陣驗欄集（A 全六欄／B 僅
  created_at NN＋禁 updated_*／deleted_*／C join 零審計欄·token 僅 created_at＋created_by
  ＋status／D 治理欄組）；soft-delete 表驗 partial-uniq WHERE deleted_at IS NULL 在場。
- Alternatives：併入 docs-sync（把 docker 依賴帶進 pre-commit 工具、否）；rust 寫閘
  （驗證工具住外層 repo、python 標準庫＝工作區工具鏈約束）。

## R5. 快照管線（brainstorm 拍板 #5＋plan 級細化）

- **refresh 子命令**：`tools/docs-sync refresh`（需 stack 在）——docker exec psql 撈
  information_schema（12 表全量欄明細：表｜欄｜序｜型別｜可空｜預設）＋帳號面三表
  （sys_user：id／user_name／nick_name／status＋角色綁定；**排除 password 欄——雜湊值
  也不入快照**）→ 寫 `docs/ops/reference-src/{schema,accounts}-snapshot.json`
  （確定性排序、追蹤、半自動材質同 events.jsonl 類）。
- **generate**：解析兩快照產 `docs/generated/reference/schema.md`＋`accounts.md`
  （stub 轉真、REFERENCE_LIVE 各加一筆——U5 預留的擴充點）；**check**：L2 對賬
  （快照↔生成物；沿 ports 的 L2 分流形）。
- **新鮮度紀律**：「加 migration 的刀必重跑 refresh→generate」守門句入活書 §8 守門表
  （本刀 T 任務落）；002 收刀時 refresh 後 diff 空＝快照與實庫一致的驗收證據。
- Alternatives：docs-sync 直連 DB（pre-commit 綁 docker、否）；解析 migration 原碼
  （脆弱、否）——brainstorm 已否決。

## R6. entity 產法（brainstorm 拍板 #4＋rev3 慣例接地）

- sea-orm-cli 1.1.20 容器內對基線庫 `generate entity` 產骨架 → 逐表手工對齊 rev3 慣例：
  檔頭 doc comment（表名＋變體）、DeriveEntityModel 形、空 Relation enum＋
  ActiveModelBehavior（rev3 sys_user.rs 實形接地）；**欄位宣告順序照 data-model §3 定稿**
  （rev3 未按表序、rev4 修齊——FR-007）。
- 型別映射：timestamptz→DateTimeWithTimeZone（chrono）、inet→IpNetwork（ipnetwork）、
  jsonb→Json；bigint→i64、smallint→i16、varchar/text→String。
- 之後手寫維護、不重生（工具僅本次 codegen 用）。

## R7. data-model 欄序基準的轉錄互驗（plan 級自拍、防轉錄誤差）

data-model §3 欄序表＝自 column-order-decisions.md 人工轉錄——轉錄本身是誤差源；
實作期第一個任務即以 `tmp/extract/scratch-columns.txt`（雙庫互證時 rev4 scratch 庫的
實際欄序 dump）機器 diff data-model §3 表格，**互驗通過後閘 2 才啟用**（憑據錯誤會讓
閘 2 反向誤判實庫）。此 dump 隨 fixtures 一併拷入。
