# Research: 003-wire-foundation

Phase 0 產出。決策面已由 brainstorm（4 題、2026-07-04）＋ADR 0025 前置解決；本檔
彙整 plan 級技術定案——含一項**實測翻案**（R1：首選抽取工具實測否決、備選轉正）。
Technical Context 零 NEEDS CLARIFICATION。實測全數於 2026-07-04 在 001 dev stack
（base-web 容器 node 26）完成、命令與輸出證據隨列。

## R1. typings→JSON Schema 抽取工具（實測定案；brainstorm 遺留必答題）

| 面向 | Decision |
|---|---|
| 工具 | **typescript-json-schema 0.67.4**（npm 最新 stable；npx 一次性、不進任何 manifest） |
| 命令形 | base-web 容器內 `/app` cwd：`npx -y typescript-json-schema@0.67.4 "src/typings/{common,api/*}.d.ts" "*" --ignoreErrors --required` |
| 抽取檔集 | api 四檔＋**src/typings/common.d.ts**（`CommonType.RecordNullable` 等 utility 命名空間住此檔——實測缺它則 api 檔解析炸 TSJ-109） |
| 輸出形 | draft-07；definitions 鍵＝完整限定名（`Api.Common.PaginatingQueryRecord` 等）；實測 35 definitions、26 個 `Api.*` 型（SystemManage 波 1 消費面全數在內） |
| 確定性 | 兩輪抽取 byte 級一致（diff 空）；輸出無產生時點欄位 |

**Rationale**: 走 TS checker 本體、吃得下編譯器懂的一切語法（含 `import('vue-router')`
內聯型）；`--ignoreErrors` 容忍 .d.ts 單獨編譯的環境噪音；exit 0＋全量 `Api.*` 實測。

**Alternatives considered**:
- **ts-json-schema-generator 2.9.0（首選案、實測否決）**：對 `declare namespace` 單檔
  可抽（`--type "*"` 綠），但對 system-manage.d.ts:92 的 `Pick<import('vue-router')
  .RouteMeta, …>` 內聯 import 型硬炸 `TSJ - 100: Unknown node "LastTypeNode"`——
  `/tmp` 與 `/app` 兩種 cwd、加 `--no-type-check` 皆同錯；該檔＝波 1 業務型所在、
  不可豁免。否。
- **tsc 自寫抽取腳本（備選 2）**：備選 1 已可行、無需動用；留作日後工具斷供退路。

## R2. rust 依賴釘版（雙查紀律）

| 依賴 | Decision | 雙查 |
|---|---|---|
| serde | 1.0.228（workspace.dependencies） | rev3 lock 現值＝crates.io 最新 stable、同值沿用 |
| serde_json | 1.0.150（同上） | 同值沿用 |
| jsonschema | 0.46.9（server dev-dependency、僅測試消費） | rev3 無前例；crates.io 最新 stable 單源（001 tower「lock 現值＝官方最新→沿用」原則的無前例變體：單源採最新 stable、回報備查） |

npm 側 typescript-json-schema 0.67.4＝npm 最新 stable（R1）；npx 一次性執行、
不進 package.json／pnpm lock——零 fork 改動維持。

## R3. rev3 形受控參照（§I.5 紀律：結構參照、全新寫、零整檔拷貝）

- `envelope.rs` 形：`Res<T>{data,code,msg}` 宣告序＝欄序、錯誤 `data:null` 不省略、
  `IntoResponse` 預設 200；`PageRes<T>` camelCase。
- `error.rs` 形：`AppError` enum 9 可發變體、保留碼**無變體**（編譯期不可構造）；
  `code()`／`key()`／`http()` 三映射烤進同檔＝映射唯一來源。
- `endpoint_coverage_lint` 形：覆蓋閘概念沿用、但 rev4 改**註冊表資料化**（R6）——
  比 rev3 的源碼掃描形更不脆弱。
- 防回歸：`From<DbErr>` 不帶入（server 今日無碼產 DbErr、不加 sea-orm 依賴——首個
  產 DbErr 的刀進場）；rev3 不存在的散裝映射自然不帶回。

## R4. router 單一來源與 demo 端點（plan 級自拍）

- **註冊表資料化**：`router.rs` 內 route 註冊表（路徑／方法／handler／contract-case
  鍵／信封例外標記）為 const 資料結構、axum Router 由它生成——覆蓋閘直接迭代資料
  結構比對 case registry（零源碼解析）。`/health` 遷入註冊表（帶例外標記、case 驗
  plain text 形）；`/metrics` 僅入 13 碼常量註記、endpoint 歸 obs 刀。
- **demo 端點**＝後端形 `GET /demo-wire`、對外形 `/api/demo-wire`（001 路由契約：
  front-nginx `location /api/` strip 前綴、後端 route 不帶 `/api`——deploy/nginx
  conf 明文；tasks 可微調名稱）：回 `Res<DemoData>`——含 string-id 欄（i64 源、
  序列化轉字串）＋`createdAt`（RFC3339 帶 offset）＋一個文字欄；msg=`common.success`。
  標記暫時物。

## R5. 序列化細節（§I.3 執行面）

- 時間欄：chrono `DateTime<Utc>`→RFC3339 帶 offset（serde 序列化形實作時以 offset
  斷言鎖住；`+00:00`／`Z` 形皆帶 offset、以 contract case 凍結實形）。
- string-id：`serialize_with` helper——i64→JSON string；number 宣告欄位 i64→JSON
  number 前過 2^53 守衛（`abs ≤ 2^53` 否則 fail-loud panic/error——寧炸不靜默失真）。
- 裁判驗證：jsonschema crate 對 draft-07 快照 definitions 解析、以
  `Api.Common.PaginatingQueryRecord` 等通用型驗 `PageRes` 序列化輸出（clarify Q1
  受審面）；泛型 `records.items` 的 `$ref: #/definitions/T` 於驗證時以具體 case
  型替換或以結構斷言涵蓋（實作細節歸 tasks）。

## R6. 守門測試形（ADR 0004 執行面）

- 13 碼 table-driven：測試側常量表（code／key／http／可發性）逐列——可發碼構造
  `AppError` 變體→`IntoResponse`→斷言 HTTP status＋信封三欄；表長恰 13、與
  data-model §1 對齊。
- 保留碼：無變體＝編譯期保證；另以矩陣列舉測完整性（`AppError` 全變體 match＋
  可發碼集合斷言恰 9、防變體被誤加）。
- offset 斷言：demo 端點響應經 serde_json 解析、時間欄 regex/解析驗帶 offset。
- 覆蓋閘：迭代 router 註冊表、逐條斷言 contract case registry 有對應鍵；例外端點
  同樣要 case（驗例外形）。
