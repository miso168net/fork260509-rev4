# ARCHITECTURE — rev4 活書（living as-built）

本書永遠現在式：只寫系統現在的樣子。未來事項住 ops/（NOTES／BACKLOG）、歷史住 git＋events；
決策全文住 decisions/、快變事實住 generated/reference/。空節代表對應子系統尚未建置、隨刀填入。

## §1 簡介與目標

rev4-admin 是一套管理後台系統：前端 fork 自 soybean-admin（Vue3＋TS＋naive-ui）、
後端以 Rust 從零重寫，經歷 rev1~rev3 三代演進後、本代自上游最新版與乾淨血緣重跑。

**能力級**（以 base-web 為權威——前端有的功能、後端必供對應端點，範圍不縮減）：
使用者／角色／選單管理、casbin RBAC（menu／button 維度）、認證與 session 治理、
系統設定、審計（操作／存取／登入嘗試）、IP 存取控制、觀測層。

**明確不做**：多租戶、對外開放 API、行動端。

**目前建置狀態**：文件地基（波 -1）就位；base-web／rust-api 程式體隨波次建置。

## §2 約束

- **技術棧**：前端＝soybean-admin fork（Vue3／TypeScript／naive-ui／vite／pnpm）；
  後端＝Rust（axum／sea-orm／PostgreSQL／Redis／casbin）；容器化 docker compose；
  工作區工具＝python3 標準庫（tools/docs-sync）。
- **repo 拓樸**：傘狀 repo（本 repo、default branch `rev4-admin-root`）＋兩個雙身分子體
  （本機 git worktree／外層 submodule gitlink）：`base-web/`（分支 `rev4-admin-base-web`、
  自 upstream example 最新 HEAD 衍生）與 `rust-api/`（分支 `rev4-admin-rust-api`、自源倉
  Initial commit 起全新寫）。fork 源倉在本機另處、gitignored 且必須保留。
- **環境**：WSL2（drvfs 掛載）；repo 全域 .gitattributes 強制 LF；host 無 rust toolchain、
  build/test 一律容器內。
- **上游關係**：upstream 常態 rebase 為預期事件；fork 差異治理見 constitution §III。

## §3 系統脈絡

（本節尚無內容；ingress 拓樸與外部依賴隨部署刀填入。）

## §4 解法策略

- **從上游重來的 fork 策略**：base-web 取上游最新 HEAD 衍生、rust-api 從零重寫；
  fork 差異以軌道制治理（constitution §III：不動 inline 為預設、★軌道逐用途授權、
  `rev4-inline` 標記紀律）。
- **傘狀雙脊椎**：傘狀 repo 管文件／spec／編排，兩子體各自成倉；兩段式 commit
  （worktree 內 commit→外層 pin bump）保證每個外層 commit 可重現。
- **縱切刀工作流**：功能以縱切刀交付（migration→facade→handler→授權→wire→前端整條打通）；
  橫切慣例為一級公民（事件 kind=horizontal）、每條慣例必附守門機制（§8）。
- **授權模型**：casbin RBAC、DB-first 寫入（寫側只動 DB、寫後全量重載——constitution §I.2
  與行為島進場規則承載細節）。
- **wire 契約機器化**：前端 typings 為裁判、contract test＋coverage gate 守恆
  （constitution §I.3）。
- **機器優先文件觀**：文件為機器與人共讀而設計；每個事實一個人寫的家、鏡像一律機器生成
  （tools/docs-sync）、契約 lint 在 commit 當下強制。

## §5 Building blocks

（本節尚無內容；crate／facade 地圖與前端結構隨對應刀填入。欄位明細住 generated/reference/schema。）

## §6 Runtime

（本節尚無內容；登入鏈／RBAC 判定鏈／狀態機圖隨行為刀填入。）

## §7 部署

（本節尚無內容；compose 拓樸與模式敘事隨部署刀填入。port／卷實值住 generated/reference/ports。）

## §8 橫切概念

每條橫切慣例必附「守門機制」——無守門的慣例是願望、不入本節。
守門標「隨◯◯刀建立」者＝該守門的落地義務綁在首個消費它的刀上（該刀 spec 必含建立守門的 task）。

| 慣例 | 規則 | 守門機制 |
|---|---|---|
| datetime | DB 時間欄一律 `timestamptz` 存 UTC；wire 一律 ISO-8601 帶時區偏移、禁 naive datetime；前端唯一 formatter util、以瀏覽器時區顯示＋帶時區標示（使用者偏好時區留參數位、消費點只有 formatter 一處） | wire 驗收含「時間欄必帶 offset」斷言（隨 wire 地基刀建立）；前端 lint 禁繞過 formatter 裸格式化（隨 base-web 首刀建立） |
| i18n | primary locale＝zh-TW（預設 UI／開發驗收基準）；zh-cn 字典保留維護＝上游 rebase 同步錨點；語言選單「簡體／繁體／English」；業務錯誤 msg＝i18n key、前端 $t 翻譯（詳 constitution §I.3 與 I18N-WIRING 軌道） | locale 對等 lint：zh-cn／zh-tw 鍵集合一致、pre-commit 擋（隨 base-web 首刀建立）；`App.I18n.Schema` 型別使「加鍵漏語言」直接 typecheck 紅 |
| 錯誤碼 | 13 碼矩陣整組凍結、新需求優先 reuse 既有碼；碼→HTTP 映射、保留碼規則、msg=key 詳 constitution §I.3 | 碼表 table-driven contract test＋「保留碼後端永不發出」斷言（隨 wire 地基刀建立）；後端錯誤型→業務碼映射收單一來源 |
| 審計欄 | 業務表建表即帶 archetype 全欄；四變體歸屬與無 retrofit 條款詳 constitution §I.6 | migration 建表檢查＋schema 往返驗證（隨 schema 基線刀建立）；`/speckit-plan` 自查第 8 題每刀必答 |
| soft-delete | 軟刪欄成對寫入（`deleted_at`＋`deleted_by` 同寫）；讀端預設過濾已刪列；軟刪表唯一鍵用 partial-uniq `WHERE deleted_at IS NULL` | partial-uniq 約束本身（DB 層直接擋重複）；facade 讀端過濾測試（隨對應 entity 刀建立）；刪除連動行為（如角色刪除清授權）隨對應刀立 ADR 入憲 |

route 全集等快變事實住 generated/reference/routes。

## §9 架構決策

決策全文住 docs/arc42/decisions/（一決策一檔）；索引住 docs/generated/DECISIONS-INDEX.md。
本節不承載內容。

## §10 品質要求

（本節尚無內容；fail-open／closed 語意總表與效能目標隨對應拍板填入。）

## §11 風險與技術債

待辦與候選 ☞ ops/BACKLOG；坑與防法 ☞ ops/LESSONS。本節不承載內容。

## §12 名詞表

- **刀**：一個 feature 的完整交付單位（brainstorm→SDD→TDD→收刀）；縱切刀＝功能縱貫、橫切刀＝慣例橫貫。
- **收刀**：feature merge 回 default branch＋簿記三步（events append＋NOTES＋generate）。
- **島**：具狀態機性質的行為子系統（如 token rotation）；其不變式經 amendment 入 constitution §I.7。
- **軌道**：constitution §III 授權的 base-web 改動邊界類別。
- **短名／長名**：目錄與口語用短名（base-web／rust-api）；git 分支用長名（rev4-admin-*）。
- **pin**：外層 repo 記錄的 submodule commit SHA；單元邊界即時 bump。
- **活書**：本檔——現在式 as-built 敘事，人寫、lint 守約。
- **事件源**：docs/ops/events.jsonl——收刀／review／里程碑的 append 型單一事實源。
- **傘狀 repo**：本 repo；只記文件、spec、gitlink pin，不含子體實碼。
