# 002-schema-baseline 刀 brainstorm — 基線 schema＋seed（user 定稿制）

日期：2026-07-04｜性質：**刀內 brainstorm**（上游輸入＝wave-0-plan §2.2＋ADR 0021／0013／
0015；ADR 0021 規定的兩個工作坊已由 user 於 rev3 session **前置完成**、本檔採認其產物）｜
方法：接地（rev3 workspace tmp/ 產物盤點＋雙庫互證報告）→ 逐題問答（6 題）→ 五節設計核可。
上游決策：ADR 0021（user 定稿制、supersedes 0014）、ADR 0013（短編號）、ADR 0015（casbin
委派建表）；本檔＝`/speckit-specify` 手動起手的 input。

## 0. 拍板紀錄

前置事實：user 於 rev3 session 完成 db 重整（欄序模板重排＋11 處改名＋3 新 memo 欄＋seed
調整），產物存 rev3 workspace `tmp/`——m001_rev3_schema.rs（615 行、11 表 terminal schema）、
m002_rev3_seeds.rs（563 行、6 表 241 列）、column-order-decisions.md（12 表逐表拍板紀錄）、
extract/（live 全量 dump 凍結檔）、VALIDATION-REPORT.md（雙庫互證八軌全綠）。

| # | 題目 | 拍定 |
|---|---|---|
| 1 | 工作坊定位 | **已前置完成、不重跑**：column-order-decisions.md（標「全 12 表拍板完成」）＋m002 定稿（db 重整後 live 逐列轉錄）＝ADR 0021 要求的「user 定稿」憑據；002 直接錄入 specs data-model.md 當凍結史料 |
| 2 | casbin 政策 seed | **入基線**（149 列隨 m002）＋立 ADR 0023——menu id↔casbin v1 引用屬同批定稿的連動一致性、拆開易斷鏈；supersedes ADR 0021「授權政策 seed 隨 casbin 進場刀」句、其餘不動 |
| 3 | 閘 1 參考基準 | **凍結 fixtures**：tmp/extract/ 拷入 specs/002 fixtures（標來源＋擷取日 2026-07-03）；離線可重跑、rev3 下線不失效；rev3 在機時驗收加跑一次 live 直比交叉驗證（防 fixtures 本身 stale） |
| 4 | entity 產法 | **生成起手＋手工對齊**：sea-orm-cli 對基線庫生成骨架→逐表對齊 rev3 entity 慣例→之後手寫維護（不重生）。生成保零過錄誤差、手工保慣例一致 |
| 5 | extractor 資料源 | **快照中繼檔**：docs-sync 新增需 stack 的 refresh 子命令（docker exec 撈 information_schema＋帳號三表→寫追蹤快照檔、材質＝半自動同 events.jsonl 類）；generate／check 離線解析快照→pre-commit 維持秒級離線 |
| 6 | sea-orm-cli 釘版 | **1.1.20**（crates.io 最新 stable；與 sea-orm-migration 1.1.20 同版配對＝codegen 產物與 runtime 型別零世代差；一次性 codegen 工具、容器內 cargo install --locked、不進 runtime 依賴） |

自拍備查（純工程、依 CLAUDE.md §5）：argon2 **0.5.3**（rev3 lock 現值＝crates.io 最新、
「lock 現值＝官方最新→沿用」原則同 001 tower 前例）；async-trait 不另引
（sea-orm-migration prelude 再匯出、tmp 雙庫互證編譯已實證）；sea-orm 1.1.20 已在 001 R1
釘定（entity crate 引用時沿 workspace 單一來源）。

## 1. tmp 產物採用與改寫（核心交付）

m001／m002 兩檔 **DDL／DML 語意零改動**採用（內容＝雙庫互證八軌全綠的定稿），僅三類改寫：

1. **檔名**：`m001_baseline_schema.rs`／`m002_baseline_seeds.rs`（ADR 0013 短編號＋語意名；
   DeriveMigrationName 使檔名成為 seaql_migrations 永久記錄名——檔名不帶前代代號）。
2. **檔頭註解改寫**：lineage 指向 `specs/002-schema-baseline/data-model.md`＋fixtures
   （交付碼零前代代號字樣、同 001 紀律）；「三類刻意差異」（欄序模板／11 改名／3 memo 欄）
   敘事全文搬進 data-model.md。
3. **依賴接線**：migration crate 加 argon2 0.5.3（workspace.dependencies 單一來源）；
   **sea-orm-adapter 自 rev3 workspace 拷入 vendored crate**（憲法 §I.5 明文例外授權；
   根直下平鋪＝001 拍板 #11 預留的零路徑轉換）；migration/src/lib.rs 依序註冊兩支。

三類刻意差異摘要（全文歸 data-model.md）：欄序模板「id → 審計六欄 → status → 業務欄」
（log 表變體無 updated/deleted）；改名 11 處（rename map 總表隨 data-model）；新增
user_memo／role_memo／menu_memo（text NULL、seed 全空）。casbin_rule 基底 8 欄由
sea_orm_adapter::up() 委派建（ADR 0015）＋ALTER 3 治理欄。

## 2. specs 資產（定稿憑據＋凍結 fixtures）

- `specs/002-schema-baseline/data-model.md`：12 表欄序定稿（自 column-order-decisions.md
  轉錄）＋rename map 總表＋新增欄總表＋seed 定稿清單（241 列：user 3／role 3／user_role 3／
  menu 78／casbin 149／settings 8；執行期生成值以規則表示、如 argon2id(123456) 隨機 salt）。
- `specs/002-schema-baseline/fixtures/`：tmp/extract/ 全套拷入（columns／constraints／
  indexes／sequences／row-counts＋6 表 seed json；檔頭標「來源＝rev3 live 2026-07-03 擷取」）
  ——閘 1 凍結對照基準。
- **ADR 0023**（隨本 brainstorm 立案）：casbin 政策 seed 移入基線。

## 3. 兩道閘＋審計守門＋快照管線

- **閘腳本**＝獨立工具（python3 標準庫＋docker exec psql；需 stack 在跑、**不進 pre-commit**；
  建議形＝tools/ 下單支、子命令分閘）：
  - 閘 1 結構零漂移：rev4 實庫 information_schema vs fixtures——rename map 雙向配對、忽略
    表內欄序、複合索引／複合主鍵內部欄序嚴格；刻意差異白名單＝3 memo 欄＋wbip_memo
    varchar→text（ADR 0021 閘 1 語意、只管結構不管 seed）。
  - 閘 2 定稿落實：實庫 ordinal_position＝data-model 排定欄序；實庫 seed 列集合＝定稿清單
    （natural key 配對；argon2 欄驗 PHC 格式非字面值）。
- **審計欄建表守門**（活書 §8「隨 schema 基線刀建立」義務清掉）：依憲法 §I.6 變體矩陣驗
  每張業務表審計欄齊備（完整六欄／log 型變體），併入閘腳本、日後每刀可重跑。
- **快照管線**（B-003／B-004 落地）：docs-sync 新增 refresh 子命令（需 stack；撈
  information_schema 全量＋sys_user／sys_role／sys_user_role 帳號面）→寫入 repo 追蹤的
  快照檔（半自動材質）→ generate 解析快照產 reference/schema＋reference/accounts
  （stub 轉真＋L2 對賬啟用）；「加 migration 的刀必重跑 refresh」紀律句入活書 §8 守門表。

## 4. entity crate

- sea-orm-cli 1.1.20（容器內、--locked）對基線庫生成 11 表＋casbin_rule 骨架→逐表手工對齊
  rev3 entity crate 慣例（inet／jsonb 型別映射、derive 集、命名）→之後手寫維護。
- workspace members 加 entity；本刀 entity **零 runtime 消費者**（003 wire 刀起接）——
  驗證＝容器內編譯＋閘 2 間接驗欄集。
- 已知坑預告（L-071）：sea-orm 若 default-features=false 無 date-time backend，timestamptz
  欄的 Model 編不過——entity crate features 對齊 rev3 解法（實作時查 rev3 entity crate 現值）。

## 5. 驗收（命令級）與收尾

1. 空庫 `up -d --wait`：migrate 跑 m001＋m002 → 11 業務表＋casbin_rule＋241 列 seed 就位、
   migrate Exited(0)、五常駐 healthy 不受影響。
2. 閘 1 綠（vs fixtures）；rev3 在機時加跑一次 live 直比交叉驗證。
3. 閘 2 綠（欄序＋seed 定稿落實）；審計欄守門綠。
4. 冪等：二次 up（ON CONFLICT DO NOTHING）不炸；`down -v` 歸零重來仍綠；
   migration down→up 對稱可逆（列數複現）。
5. 容器內 `cargo test --workspace` 全綠（含 entity 編譯）。
6. 文件面：refresh→generate→check 全綠；reference/schema＋accounts 轉真
   （STATE 對賬區剩 routes／screens 兩 stub）。
7. 不變式：base-web 零改動（pin 不動）；rev3 stack 無擾動。

**B-024 處置**：本刀＝承襲 rev3 形＋user 定稿、非 IP 取證欄重設計——B-024 觸發語調整為
「首次重設計 IP 取證欄形的刀」、條目保留不刪（隨本 brainstorm 微調 BACKLOG 行）。

**收刀簿記**：per-unit pin bump（rust-api 兩段式）→活書 §5（entity／crate 地圖首填）與
§8 守門表更新【feature branch 內改】→BACKLOG 刪 B-003／B-004→merge --no-ff（需 user 同意）
→events feature_close＋NOTES 指 003＋generate 一筆簿記 commit。

## 6. 對上游規劃的修正點

1. ADR 0021 兩個「brainstorm 內建工作坊」：實際由 user 於 rev3 session 前置完成（產物＝
   拍板紀錄檔＋定稿轉錄碼＋互證報告），002 採認產物、不重跑——工作坊「內建於 brainstorm」
   的字面形式被前置形式取代，定稿制精神不變。
2. casbin 政策 seed 歸屬：wave-0-plan §2.2／ADR 0021「隨 casbin 進場刀」→改「入基線」
   （ADR 0023、連動一致性理由）。
3. wave-0-plan 留刀內三題（欄序呈現形式／參考庫來源／entity 產法）全數落定（見 §0 拍板表）。

## 7. SDD 接續

本檔＝`/speckit-specify` 的 input；specify 由 user 手動起手（CLAUDE.md §2：確保
feature-branch pre-hook 生效）。TDD 實作照 CLAUDE.md §2 編排範本（Workflow 每執行單元一支；
rust 全程容器內 serial；review agent 只讀；絕不 push/merge）。
