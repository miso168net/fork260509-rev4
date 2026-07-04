# Tasks: 003-wire-foundation 統一信封＋13 碼守門＋契約機器化骨架

**Input**: Design documents from `/specs/003-wire-foundation/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md
（全數就緒）；001 dev stack 在跑（五常駐 healthy）

**Tests**: 含測試任務——TDD 為憲法 §I.4 強制：信封／錯誤模組與 tools/wire-schema 走
單元測試先行（紅→綠）；三類守門與覆蓋閘**本身即交付物**（測試＝產品、有效性由驗收
段負面自證）；驗收命令級（quickstart.md 即測試腳本、contracts/ 即比對契約——001/002
同口徑）。

**Organization**: 任務按 user story 分組；驗收語意以 spec.md 為準、命令形以
quickstart.md 為準、比對規則以 contracts/ 為準、機器基準以 data-model.md 為準。

## 硬約束（烤入所有任務）

- rust build／test **全程容器內、全程 serial**（host 無 toolchain；平行 cargo 互撞
  target）：`docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T
  rust-api cargo …`。
- **base-web 零 fork 改動**（FR-012）：typings 唯讀抽取、npx 一次性不碰
  package.json／pnpm lock；前端 porcelain 前後皆空。
- 版本一律照 research.md R2 釘死（serde 1.0.228／serde_json 1.0.150／jsonschema
  0.46.9 dev-dep／typescript-json-schema 0.67.4 npx）；**絕不引入浮動版本**。
- rev3 形＝**受控參照**（§I.5：結構參照、全新寫、零整檔拷貝）；參照面不足或發現
  rev3 形有疑義＝回報主線、不得自行擴參照範圍。
- 交付碼（server 新模組／測試、tools/wire-schema）**零前代 workspace 代號字樣**
  （FR-013；lineage 指 specs/ADR）。
- 13 碼矩陣照 data-model §1 逐字（constitution §I.3 凍結）；發現矩陣疑義＝回報、
  不得自行改碼表。
- 本清單**不含 push／merge**（finishing 階段、需 user 同意——CLAUDE.md 硬禁令）。
- rust-api worktree 內每個執行單元收尾：worktree commit → 外層 pin bump（兩段式
  commit）。
- demo 端點＝暫時物（檔頭標注；刪除待辦於 Polish 登記）；負面注入驗畢必還原、
  終態樹淨全綠。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: rust 依賴接線——全部後續任務的編譯前提

- [ ] T001 rust-api workspace 依賴接線：`rust-api/Cargo.toml` [workspace.dependencies]
      加 serde = { version = "1.0.228", default-features 照需 }＋serde_json =
      "1.0.150"；`rust-api/server/Cargo.toml` 引 serde（workspace=true、derive）＋
      serde_json（workspace=true）、[dev-dependencies] 加 jsonschema = "0.46.9"；
      容器內 `cargo build` 過

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 信封＋錯誤模組——US1 的本體、US2/US3 守門的受測對象

**⚠️ CRITICAL**: 本階段完成前不得進任何 user story

- [ ] T002 【測試先行】信封單元測試先紅：`rust-api/server/src/envelope.rs` 內
      #[cfg(test)]（沿 001 server 既有形）——欄序 data→code→msg（序列化輸出逐字）、
      code 為 JSON string、錯誤 data:null 不省略、無 success 欄、PageRes camelCase
      ＋空頁 records:[]＋無 pages、2^53 守衛 fail-loud、string-id helper（i64→JSON
      string）；先確認紅（模組未實作）
- [ ] T003 `rust-api/server/src/envelope.rs` 實作至綠：Res<T>／PageRes<T>／
      IntoResponse（預設 200）／序列化守衛 helper（contracts/envelope-contract.md
      §1／§3；結構參照 rev3 形、全新寫）；容器內 cargo test 綠
- [ ] T004 【測試先行】錯誤面測試先紅：13 碼 table-driven（測試側常量表與
      data-model §1 逐列對齊、表長恰 13；可發碼構造變體→IntoResponse→斷言 HTTP
      status＋信封三欄）＋保留碼列舉完整性（可發碼集合恰 9、7778/8889/9998/9999
      無變體）＋HTTP 例外恰 4040→404、5003→403
- [ ] T005 `rust-api/server/src/error.rs` 實作至綠：13 碼常量表＋AppError 9 變體
      （碼／key／http 烤進變體、data-model §1 逐字）＋IntoResponse 建錯誤信封
      （data:null 不省略）；`From<DbErr>` 不實作（research R3 防回歸）；容器內
      `cargo test --workspace` 全綠（既有測試不退化）

**Checkpoint**: 信封＋錯誤骨架就緒；rust-api worktree commit＋外層 pin bump

---

## Phase 3: User Story 1 - 一致的 wire 形（統一信封＋錯誤碼骨架） (Priority: P1) 🎯 MVP

**Goal**: 端到端可驗的信封實形——router 單一來源＋demo 端點＋錯誤 fallback

**Independent Test**: quickstart A＋B（對外形信封實測、直連等價、/health plain
text、404 fallback 錯誤信封）

- [ ] T006 [US1] router 註冊表資料化：`rust-api/server/src/router.rs`——註冊表
      const 資料（path／method／case 鍵／信封例外標記，data-model §4）→ 生成 axum
      Router；`/health` 遷入註冊表（例外標記）；fallback→AppError::NotFound
      （4040→404）；lib.rs／main.rs 接線（最小改）；【測試先行】註冊表→Router
      生成的單元測試（fallback 形、/health plain 200）先紅→實作綠
- [ ] T007 [US1] demo 端點：`rust-api/server/src/handler/demo.rs`——GET `/demo-wire`
      （後端形；對外＝/api/demo-wire——001 路由契約 strip 前綴）回 Res<DemoData>
      （id: i64 源轉 JSON string、name、createdAt: RFC3339 帶 offset；msg=
      common.success——data-model §5）；註冊表加條目＋case 鍵；檔頭標暫時物；
      容器內 cargo test 綠
- [ ] T008 [US1] 驗收（quickstart A＋B 逐字）：42080 對外形信封實形（欄序／code
      string／msg key／offset／string-id）＋42079 直連等價抽驗＋/health plain text
      ＋未知路由 404＋4040 錯誤信封（data:null 不省略）；證據留驗收紀錄

**Checkpoint**: MVP 成立——wire 形端到端可驗；rust-api worktree commit＋pin bump

---

## Phase 4: User Story 2 - 凍結不變式三類守門機器化 (Priority: P2)

**Goal**: 三類守門成為可重跑交付物（測試即產品）＋contract case registry 骨架

**Independent Test**: quickstart C 守門子集（容器內 cargo test 全綠）＋負面自證

- [ ] T009 [US2] contract case registry 骨架＋整合測試落位：`rust-api/server/tests/`
      新增守門測試檔（檔名實作定、沿 001 tests/health.rs 形）——case 鍵→驗證函式
      registry（contracts/contract-machinery.md §3 消費形）；13 碼 table-driven 與
      保留碼完整性（Phase 2 已立）掛入 registry 鍵
- [ ] T010 [US2] 時間欄 offset 斷言 case：demo 響應（in-process 呼叫、001 health
      整合測試形）時間欄解析驗 RFC3339 帶 offset（naive＝紅）；掛 registry
- [ ] T011 [US2] 驗收（quickstart C 守門子集）：容器內 `cargo test --workspace`
      全綠；負面自證＝暫時改壞一處（demo 時間欄改 naive 形）→offset 守門紅→還原
      →綠（驗畢樹淨）；證據留驗收紀錄

**Checkpoint**: 三類守門落地可重跑；rust-api worktree commit＋pin bump

---

## Phase 5: User Story 3 - 契約機器化骨架（typings 裁判＋覆蓋閘） (Priority: P3)

**Goal**: wire-schema 快照管線＋契約裁判（通用形受審）＋覆蓋閘——ADR 0025 執行面

**Independent Test**: quickstart D（extract→diff 空→負面攔截）＋C 全段

- [ ] T012 [US3] 【測試先行】`tools/wire-schema` 自帶測試先紅（test 子命令、
      unittest、離線——沿 docs-sync／schema-gate 先例形）：npx 命令組裝（釘版
      0.67.4、檔集 {common,api/*}.d.ts、--ignoreErrors --required）、原子替換、
      缺 stack fail-loud（非零退出＋提示啟動命令）、輸出路徑
      rust-api/server/tests/fixtures/wire-schema.json
- [ ] T013 [US3] `tools/wire-schema` extract 實作至綠（python3 標準庫、shebang＋
      exec bit——contracts/contract-machinery.md §1）；首抽落檔 fixtures/
      wire-schema.json（基準：35 definitions、26 個 Api.* 型——research R1 實測值，
      漂移＝回報）＋再抽 byte diff 空證據＋base-web porcelain 空證據
- [ ] T014 [US3] 【測試先行】契約裁判測試：`rust-api/server/tests/` 讀 fixtures
      快照——通用形受審（PageRes 序列化輸出 vs Api.Common.PaginatingQueryRecord
      等通用型；$ref T 處理照 research R5）＋機制自測（快照缺失 fail-loud 指名
      補救命令、draft-07 解析）；先紅（快照消費碼未實作）→實作至綠（jsonschema
      0.46.9 dev-dep）
- [ ] T015 [US3] 覆蓋閘測試：迭代 router 註冊表 vs contract case registry **雙向**
      （缺 case 紅指名路由、殭屍 case 紅指名——contracts/contract-machinery.md §3）；
      信封例外端點不豁免（/health case 驗 plain text 形）
- [ ] T016 [US3] 驗收（quickstart D＋C 全段逐字）：extract→再抽 diff 空；覆蓋閘
      負面（暫時移除 demo case→紅指名→還原→綠）；容器內 `cargo test --workspace`
      全綠（三類守門＋覆蓋閘＋契約裁判在內）；證據留驗收紀錄

**Checkpoint**: 全部 story 完成；rust-api worktree commit＋pin bump（T013 的
fixtures 隨 worktree、tools/wire-schema 隨外層——兩段式照舊）

---

## Phase 6: Polish & Cross-Cutting

- [ ] T017 活書更新（feature branch 內改）：`docs/arc42/ARCHITECTURE.md` §8——
      錯誤碼列與 datetime 列守門「隨 wire 地基刀建立」標記清掉（轉已就位形、寫
      實際守門命令）＋新增 wire-schema 快照新鮮度列（動 typings／加 route 的刀必
      於單元邊界重跑 `python3 tools/wire-schema extract` 並隨 commit）；§5 crate
      地圖 server 句對齊（信封／錯誤／router 一句話級）；現在式、lint 綠
- [ ] T018 [P] `docs/ops/BACKLOG.md`：B-001 觸發字樣改「rust-api 首個**業務**路由
      落地時」＋B-009 觸發字樣改「首個帶 facade 的功能刀 brainstorm」（brainstorm
      §6 判定）＋新增 B-NNN「刪 demo 驗證端點（連 case 與註冊表條目）｜首個功能刀」
      （next-id 取號 bump）
- [ ] T019 收官驗證：quickstart A~E 全段重跑一遍過＋容器內 `cargo test --workspace`
      全綠＋`docs-sync generate && check && lint` 全綠＋機器自檢 FR-013：grep 前代
      workspace 代號於本刀新寫交付碼（server 新模組與測試／tools/wire-schema）
      零命中＋base-web porcelain 空、pin 停 9c6f223＋rev3 容器對照無異狀；
      **quickstart F 段（波 0 出口六組檢查表整波重跑、含第 1 組 down -v 歸零）
      全綠**——SC-007、收 003 即波 0 收口判定

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 → Phase 2 → Phase 3（US1）**：嚴格串行；T001 是編譯前提、Phase 2 是
  US1 本體地基、US1 是 US2/US3 的受測對象。
- **US2（Phase 4）**：依賴 US1（demo 響應是 offset 斷言的受測物；registry 掛
  Phase 2 既有守門）。
- **US3（Phase 5）**：T012/T013（wire-schema 工具、外層 python）與 rust 面無編譯
  依賴、可在 US2 期間交錯；T014 依 T013（要快照）＋T009（registry 形）；T015 依
  T006（註冊表）＋T009（registry）。
- **Phase 6**：全 story 完成後。

### 任務級關鍵依賴

- T002→T003；T004→T005（紅→綠對）；T003 是 T004 的前提（IntoResponse 依 Res）
- T006 依 T005；T007 依 T006；T008 依 T007
- T009 依 T005＋T008；T010 依 T007；T011 依 T009＋T010
- T012→T013；T014 依 T013＋T009；T015 依 T006＋T009；T016 依 T014＋T015
- T017∥T018 可並行；T019 依全部

### Parallel Opportunities

- T012/T013（外層 python、零 cargo）可與 Phase 4 交錯（**cargo 執行一律排隊**——
  L-007）；T017∥T018；其餘 rust 面任務串行。

## Implementation Strategy

- **MVP＝Phase 1→2→3（T001~T008）**：wire 形端到端可驗即是可交付增量。
- **每執行單元**（依 CLAUDE.md §2 編排 v2：implementer→spec-compliance review→fix→
  code-quality review→fix；防呆五件套＋看門狗）收尾即 commit；rust-api 改動走
  兩段式 commit＋pin bump。
- 負面自證（T011/T016）必還原、三樹終態乾淨；quickstart F 段整波重跑收在 T019
  （收刀簿記與 push/merge 歸 finishing、不在本清單）。
