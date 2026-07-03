# Tasks: 002-schema-baseline 基線 schema＋seed（user 定稿制）

**Input**: Design documents from `/specs/002-schema-baseline/`

**Prerequisites**: plan.md、spec.md、research.md、data-model.md、contracts/、quickstart.md
（全數就緒）；001 dev stack 可用（migrate 閘門、機密、compose）

**Tests**: 含測試任務——TDD 為憲法 §I.4 強制（rust 碼與 docs-sync python 碼測試先行）；
migration／entity 屬「無獨立單元測面」的宣告型碼：其驗證＝兩道閘＋審收命令級任務
（contracts/gates.md 即測試契約、quickstart 即測試腳本——001「infra 資產命令級驗證」
同口徑）；docs-sync 新來源沿 U5 前例測試先行。

**Organization**: 任務按 user story 分組；驗收語意以 spec.md 為準、命令形以 quickstart.md
為準、比對規則以 contracts/ 為準、定稿以 data-model.md 為準。

## 硬約束（烤入所有任務）

- rust build／test **全程容器內、全程 serial**（host 無 toolchain；平行 cargo 互撞 target）：
  `docker compose -f docker-compose.yml -f docker-compose.dev.yml exec -T rust-api cargo …`。
- **base-web 零 fork 改動**（FR-011）；rev3 stack 唯讀不擾動（fixtures 拷入與 gate1
  --live-rev3 皆唯讀）。
- 版本一律照 research.md R1；**絕不引入浮動版本**；vendored sea-orm-adapter 整檔拷入
  ＝憲法 §I.5 明文例外。
- 交付碼（migration／entity／閘腳本／docs-sync 增量）**零前代 workspace 代號字樣**
  （FR-012；lineage 指 specs/ADR）。
- migration 兩檔＝tmp 定稿產物 **DDL／DML 語意零改動**採用（research R2：僅檔名／檔頭
  lineage／依賴接線三類改寫）；發現內容級問題＝回報主線、不得自行改語意。
- 本清單**不含 push／merge**（finishing 階段、需 user 同意——CLAUDE.md 硬禁令）。
- rust-api worktree 內每個執行單元收尾：worktree commit → 外層 pin bump（兩段式 commit）。
- 閘腳本（tools/schema-gate）與 refresh 需 stack 在跑；絕不接入 pre-commit（FR-014）。

## Format: `[ID] [P?] [Story] Description`

## Phase 1: Setup

**Purpose**: 定稿資產拷入＋轉錄互驗＋rust workspace 接線

- [ ] T001 [P] fixtures 拷入：rev3 workspace `tmp/extract/` **目錄整拷（26 檔、含
      scratch-* 全套）**至 `specs/002-schema-baseline/fixtures/`＋新增 `fixtures/README.md`
      （標「來源＝rev3 live、擷取 2026-07-03、閘 1 凍結基準；scratch-columns.txt＝R7
      互驗基準；seed 總數實測 244」）；檔案 byte 級原樣、不改寫
- [ ] T002 轉錄互驗（research R7、閘 2 前置）：以 `fixtures/scratch-columns.txt` 機器 diff
      `specs/002-schema-baseline/data-model.md` §3 十二張欄序表（表×欄名×序全配對）；
      不一致＝修 data-model 轉錄（scratch dump 為準、因其=雙庫互證過的實態）並記錄修正處；
      互驗證據（diff 空輸出）留驗收紀錄
- [ ] T003 rust-api workspace 接線：vendored `sea-orm-adapter/` 自 rev3 workspace 的
      `rust-api/sea-orm-adapter/` 整檔拷入 rev4 rust-api 根（§I.5 例外；根直下平鋪）；`rust-api/Cargo.toml` members 加 sea-orm-adapter、
      `[workspace.dependencies]` 加 argon2="0.5.3"＋sea-orm={version="1.1.20",
      default-features=false}；容器內 `cargo build` 過（entity member 隨 T013 加）

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: migration 兩支落檔——全部 user story 的地基

**⚠️ CRITICAL**: 本階段完成前不得進任何 user story

- [ ] T004 `rust-api/migration/src/m001_baseline_schema.rs` 落檔：tmp `m001_rev3_schema.rs`
      DDL 語意零改動遷入；改寫三類（research R2）——檔名如上、檔頭 lineage 指
      specs/002-schema-baseline/data-model.md＋fixtures（零前代代號、三類刻意差異敘事
      歸 data-model §2）、`migration/Cargo.toml` 加 argon2（workspace=true）＋
      sea-orm-adapter（path="../sea-orm-adapter"）；`lib.rs` 註冊 m001；容器內編譯過
- [ ] T005 `rust-api/migration/src/m002_baseline_seeds.rs` 落檔：tmp `m002_rev3_seeds.rs`
      DML 語意零改動遷入、同三類改寫（seed 來源註解改指 fixtures json）；`lib.rs` 依序
      註冊 m002；容器內 `cargo build`＋`cargo test --workspace` 過（既有 6 測不退化）

**Checkpoint**: migration 就緒；rust-api worktree commit＋外層 pin bump

---

## Phase 3: User Story 1 - 一鍵得到完整基線資料庫 (Priority: P1) 🎯 MVP

**Goal**: 空庫一鍵起→12 表＋244 列定稿 seed 就位；冪等可逆

**Independent Test**: quickstart A＋D 全段（乾淨狀態起、計數與格式驗證、二次套用、
down→up、down -v 重來）

- [ ] T006 [US1] 驗收（quickstart A）：`down -v`→`up -d --wait` 退出碼 0、五 healthy＋
      migrate Exited(0)；`\dt` 見 11 業務表＋casbin_rule＋seaql_migrations（記錄恰
      m001_baseline_schema／m002_baseline_seeds 兩筆）；六表計數 3/3/3/78/149/8；
      argon2 格式計數 3（零明文）
- [ ] T007 [US1] 驗收（quickstart D）：`up -d --force-recreate migrate` 二次套用零變化
      （`docker wait` 驗退出碼 0）；容器內 migration CLI `down -n 2` 全卸（含 adapter
      down；中間觀測 `\dt` 只剩 seaql_migrations、防半卸假綠）→`up` 重套→計數複現；
      `down -v` 歸零重來仍全綠

**Checkpoint**: MVP 成立——資料層地基可用

---

## Phase 4: User Story 2 - 閘 1 結構零漂移 (Priority: P2)

**Goal**: 忠實 squash 機器可證（vs 凍結 fixtures；rev3 在機時 live 交叉）

**Independent Test**: quickstart B（gate1 綠＋負面注入紅＋live 交叉輪）

- [ ] T008 [US2] `tools/schema-gate` 骨架＋`gate1` 子命令實作（python3 標準庫；契約＝
      contracts/gates.md §1／§2：rename map 14 組映射、欄序不敏感、複合索引欄序嚴格、
      白名單恰 4 項、退出碼 0/1/2、`--live-rev3` 形含 rev3 缺席 exit 2）；【測試先行】
      純函式面（rename 映射、欄名去引號正規化、白名單判定）先寫單元測試紅→實作綠；
      對現行基線庫實跑綠
- [ ] T009 [US2] 驗收（quickstart B）：gate1 綠（逐表結論）；負面＝暫 ALTER ADD COLUMN
      →gate1 紅指名→DROP 還原→綠；rev3 在機時 `gate1 --live-rev3` 交叉輪結論一致

**Checkpoint**: 結構忠實性閘落地

---

## Phase 5: User Story 3 - 閘 2 定稿落實＋審計欄守門 (Priority: P3)

**Goal**: 欄序與 seed 定稿機器驗證落實；憲法 §I.6 守門自本刀可重跑

**Independent Test**: quickstart C（gate2＋audit 綠＋負面注入還原）

- [ ] T010 [US3] `schema-gate gate2` 子命令實作（契約 §3：ordinal_position vs data-model §3
      markdown 表解析、seed vs fixtures 六支 json natural-key 配對、PHC 格式規則、
      審計時間戳排除、jsonb 正規化）；【測試先行】純函式面（markdown 表解析、natural
      key 配對、正規化）先紅→實作綠；對現行基線庫實跑綠
- [ ] T011 [US3] `schema-gate audit` 子命令實作（契約 §4：變體矩陣 A×5／B×3／C×2／D×2
      逐表驗、partial-uniq 在場驗、清單外業務表 FAIL）＋建立
      `docs/ops/reference-src/archetype-map.json`（初始內容＝data-model §1 轉錄；audit
      與 docs-sync generate 同源消費）；【測試先行】變體判定純函式先紅→實作綠；實跑綠
- [ ] T012 [US3] 驗收（quickstart C）：gate2＋audit 綠；gate2 負面＝暫 DELETE 一列
      system_settings（setting_key='password_min_length'）→gate2 紅指名→還原＝容器內
      migration CLI `down`（回捲 m002）→`up`（重放補回；重跑 migrate 服務＝no-op 不可用）
      →綠；audit 負面＝主庫暫建未登記 probe 表 t_audit_probe→audit 紅（清單外業務表）
      →DROP 還原→綠

**Checkpoint**: 兩道閘＋守門全數落地（gate 語意詳 contracts、後刀可重跑）

---

## Phase 6: User Story 4 - entity 層 (Priority: P4)

**Goal**: 13 檔 entity 與定稿逐欄一致、隨 workspace 編譯

**Independent Test**: cargo test --workspace 全綠＋欄集對照

- [ ] T013 [US4] entity 骨架生成：容器內 `cargo install sea-orm-cli --version 1.1.20
      --locked`＋對基線庫 `generate entity` 產骨架至暫存；建 `rust-api/entity/` crate
      （Cargo.toml：sea-orm workspace=true＋features=["macros","with-chrono","with-json",
      "with-ipnetwork"]——research R6／L-071）；workspace members 加 entity；容器內編譯過
- [ ] T014 [US4] entity 逐表對齊：12 表＋lib.rs——欄位宣告順序照 data-model §3、rev3 慣例
      形（檔頭 doc comment 標表名＋變體、DeriveEntityModel、空 Relation＋
      ActiveModelBehavior）、型別映射照 research R6；欄名集合 vs data-model §3 逐表核對
      （證據留驗收紀錄）；容器內 `cargo test --workspace` 全綠

**Checkpoint**: 003+ 的消費介面就緒；rust-api worktree commit＋pin bump

---

## Phase 7: User Story 5 - 快照管線與正典文件 (Priority: P5)

**Goal**: B-003／B-004 落地——reference/schema＋accounts stub 轉真、L2 對賬

**Independent Test**: quickstart F（refresh→generate→check 綠＋漂移攔截＋新鮮度證據）

- [ ] T015 [US5] 【測試先行】tools/docs-sync 新增 refresh 測試（TestSnapshot 類：快照
      確定性排序、密碼欄排除斷言、缺 stack fail-loud、原子替換）——先紅
- [ ] T016 [US5] `docs-sync refresh` 子命令實作至綠（契約 snapshot-reference.md §1：
      docker exec psql 撈 information_schema＋帳號三表→寫
      `docs/ops/reference-src/{schema,accounts}-snapshot.json`）；測試轉綠
- [ ] T017 [US5] 【測試先行→實作】generate／check 兩來源：先加測試（快照解析→兩表生成、
      確定性、REFERENCE_LIVE 轉真、L2 分流、快照缺失 fail-loud、archetype-map 缺表
      fail-loud）確認紅→實作至綠（契約 §2；REFERENCE_LIVE 加 schema＋accounts 兩筆、
      STATE 對賬區轉真；reference/schema 每表標 archetype 歸屬——來源＝
      docs/ops/reference-src/archetype-map.json）；`docs-sync test` 全套綠
- [ ] T018 [US5] 驗收（quickstart F）：refresh→generate→check 全綠；STATE 對賬剩
      routes／screens 兩 stub；漂移攔截＝手改快照不 generate→check 紅→還原→綠；
      新鮮度證據＝再跑 refresh 後 `git diff docs/ops/reference-src/` 空

**Checkpoint**: 全部 story 完成

---

## Phase 8: Polish & Cross-Cutting

- [ ] T019 活書更新（feature branch 內改）：`docs/arc42/ARCHITECTURE.md` §5 首填
      crate 地圖（server／migration／entity／sea-orm-adapter 一句話級、明細與變體歸屬
      指 reference/schema）＋§8 守門表——審計欄守門列改「已建立＝tools/schema-gate
      audit」、新增快照新鮮度守門句（加 migration 的刀必 refresh→generate）、新增
      「欄序＝基線刀 user 定稿、後續加欄一律 append」句（ADR 0021 修訂一義務）；
      現在式、零欄位明細字面
- [ ] T020 [P] `docs/ops/BACKLOG.md` 刪 B-003、B-004 列（完成即刪；next-id 不動）
- [ ] T021 收官驗證：quickstart A~G 全段重跑一遍過（含 G 段：base-web porcelain 空＋
      pin 停 9c6f223、rev3 容器基線對照無異狀、`down`→`time up -d --wait` 熱起 ≤5min
      ——001 SC-007 迴歸）＋容器內 `cargo test --workspace` 全綠＋
      `docs-sync generate && check && lint` 全綠＋機器自檢 FR-012：grep 前代 workspace
      代號於本刀新寫交付碼（migration 兩支／entity／tools/schema-gate／docs-sync 本刀
      diff）零命中（vendored sea-orm-adapter 豁免——§I.5 整檔拷貝例外、內容不改寫）

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 → Phase 2 → Phase 3（US1）**：嚴格串行；T002 互驗是閘 2（US3）的啟用前提、
  T003 是 T004 的編譯前提；US1 是其餘 story 的運行前提（基線就位才有比對對象）。
- **US2／US3（Phase 4~5）**：都只依賴 US1 完成後的基線庫；gate1 與 gate2/audit 同住
  一支腳本——T008 先立骨架、T010/T011 疊加子命令（檔案級串行）。
- **US4（Phase 6）**：僅依賴 US1（codegen 要活庫）；與 US2/US3 無互依、順序可換
  （cargo 執行本身 serial）。
- **US5（Phase 7）**：refresh 依賴 US1 活庫；與 US2~US4 無互依。
- **Phase 8**：全 story 完成後。

### 任務級關鍵依賴

- T002 依 T001；T004 依 T003；T005 依 T004；T006 依 T005；T007 依 T006
- T008 依 T006（要有綠基線可比）＋T001；T009 依 T008
- T010 依 T008（腳本骨架）＋T002（互驗過）；T011 依 T008；T012 依 T010＋T011
- T013 依 T006（活庫 codegen）；T014 依 T013
- T015→T016（紅→綠）；T017 依 T016；T018 依 T017；T015 依 T006（refresh 要活庫）
- T021 依全部

### Parallel Opportunities

- Phase 1：T001 與 T003 可並行（不同 repo、無 cargo 衝突）；T002 需 T001
- US2~US5 彼此獨立、可依編排單元交錯；**但 cargo 執行一律排隊**（T013/T014 與任何
  rust 面任務不並行）、tools/schema-gate 三子命令同檔串行
- Phase 8：T019∥T020

## Parallel Example: Phase 1

```text
# 不同倉並行（無共用檔、無 cargo 競爭）：
Task: "T001 fixtures 拷入（外層 specs/）"
Task: "T003 rust-api workspace 接線（worktree；容器內 cargo build serial）"
# T002 等 T001 完成後執行
```

## Implementation Strategy

- **MVP＝Phase 1→2→3（T001~T007）**：基線就位即是可交付增量；停下驗證後再推閘與管線。
- **每執行單元**（依 CLAUDE.md §2 編排：implementer→spec-compliance review→fix→
  code-quality review→fix）收尾即 commit；rust-api 改動走兩段式 commit＋pin bump。
- 閘負面注入（T009/T012/T018）必還原、三樹終態乾淨；audit 負面用 scratch 庫防污染。
- US5 動 tools/docs-sync 屬外層純工具碼、沿 U5 TDD 前例。
