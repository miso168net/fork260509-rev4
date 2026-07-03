# Research: 001-compose-stack

Phase 0 產出。所有技術未知已於刀內 brainstorm 階段以「查 rev3 現值＋官方最新（2026-07-03
查證：rust-lang.org／crates.io API／Docker Hub API／npm registry，tag 逐一驗存在）＋user
逐題拍板」解決——本檔為彙整；Technical Context 零 NEEDS CLARIFICATION。
拍板全文與對照表＝`docs/brainstorms/001-compose-stack.md` §0／§1（凍結）。

## R1. 版本釘定（brainstorm 拍板 #1~#10）

| 元件 | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| Rust toolchain | 1.96.1 | 官方最新 stable；001 全新 scaffold 無 rev3 的 jsonwebtoken→time MSRV 包袱；新專案起在最新、後續刀引依賴不先撞 MSRV | 1.86.0（rev3 現值）：與 rev3 同版但起步即落後十個 minor |
| axum | 0.8.9 | 最新 stable；波 0 不裝 metrics、無 rev3 的 axum-prometheus 0.7 天花板；從零寫零遷移成本 | 0.7（rev3 現值）：可逐字參照 rev3 但背新遷移債 |
| sea-orm＋-migration | 1.1.20（同版配對） | rev3 現值＝官方最新 stable 同一版；002 刀參照 rev3 migration 寫法 API 零差異 | 2.0.0-rc.41：pre-release、違全域釘版紀律 |
| tokio | 1.52.3 | rev3 lock 現值＝官方最新，零爭議 | 只寫 major 交 lock 浮動：violates 釘版制度 |
| dev 熱重載 | watchexec-cli 2.5.1 | cargo-watch 已 archived（維護者指名接棒者）；無 TTY 需求、支援 `--poll`（WSL2 必須） | cargo-watch 8.5.3（rev3 現值、已死線）；bacon 3.23.0（TUI-first、不合 headless 容器） |
| postgres | 18.4-alpine | 最新 major 最新版、已到 .4；002 閘 1 參考庫在 rev4 側同版容器重放、major 差異不構成比對雜訊 | 17.10-alpine（rev3 同 major）：零重放風險但日後帶資料升 major |
| redis | redis:8.8.0-alpine、服務名 `redis` | redis-stack 產品線已棄用（停 7.4、永無 8）；Redis 8 官方合併路線、Stack modules 內建；rev3 僅用核心＋pub/sub 功能面零影響 | redis-stack-server:7.4.0-v8（rev3 現值、死線） |
| nginx | 1.31.2-alpine | 沿 rev3 的 mainline 線升至線上最新；官方對一般使用者建議線 | 1.30.3-alpine（stable 線）：比 rev3 現值還舊 |
| node | 26.4.0-alpine | 沿 rev4 example compose 既有拍板、master 與 example 同版 | 24.18.0-alpine（LTS）：推翻既有拍板需連動改 example |
| pnpm | 10.34.3 | 10 線最新；base-web 的 pnpm-lock.yaml 屬 pnpm 10 世代、engines `>=10.5.0` 滿足；零 lockfile 風險 | 11.9.0：新 major 可能重寫 lockfile、破 base-web 零改動不變式 |

次要 crate 版本查證（rev3 lock 現值恰為官方最新）：tracing 0.1.44、tracing-subscriber
0.3.23——001 實際引用（server log）。serde 1.0.228、serde_json 1.0.150、toml 0.8.23——
**001 無消費者、不入 workspace.dependencies**（/health 為 plain text 無 JSON 序列化、001 無
toml 設定檔）；隨首個消費者刀進場、屆時重走釘版程序，查證值留此備查。

## R2. 結構拍板（brainstorm 拍板 #11~#13）

- **workspace 佈局＝根直下平鋪**（server/、migration/）。Rationale：與 rev3 同形、參照與
  vendored crate 進場零路徑心算。Alternative：crates/ 子目錄（持續付對照稅）。
- **healthcheck＝全沿 rev3 數值、只改探針 port**。Rationale：數值為 rev3 實機磨合（rust-api
  retries 12＋start 120s＝cargo 冷編實測）。Alternative：重訂參數（無實據）。
- **standalone compose 不帶入**。Rationale：rev3 已標 DEPRECATED、共卷互踩；
  `docker compose up <service>` 已可子集啟動。Alternative：裁剪帶入（維護兩支多餘檔）。

## R3. plan 級技術決定（本刀內自拍、依 CLAUDE.md §5 回報備查）

1. **Debian base 對齊**：`rust:1.96.1-slim` 底層＝Debian 13 trixie；001 只建 dev stage，
   部署刀建 runtime 時必須配 `debian:trixie-slim`（glibc 同代；rev3 先例 bookworm 對
   bookworm）。已記入 brainstorm §1 與 Dockerfile 檔頭註解義務。
2. **watchexec 啟動形**：`watchexec -r -e rs,toml --poll 1s -- cargo run --bin server`——
   `-r` 重啟 long-running、`-e rs,toml` 監源碼與 manifest、`--poll 1s` 因 WSL2 bind-mount
   inotify 不可靠（rev3 實測）且 watchexec 預設 30s 太鈍、取 cargo-watch 舊預設 1s。
3. **compose target 下放模式**：001 Dockerfile 僅 dev stage → base 層 build 不給 target、
   dev override 給 `target: dev`（rev3 migrate service 既有模式）；避免 base 層引用不存在
   的 runtime stage。
4. **`init: true`（dev rust-api）**：watcher 不宜當 PID 1（watchexec／cargo-watch 文檔皆
   提醒）、tini 接管訊號轉發；rev3 未做、rev4 一次做對。
5. **Cargo manifest 慣例**：`[workspace.dependencies]` 版本單一來源＋完整三段版號＋
   `[workspace.package] edition = "2024"`（1.96 已 stable；rev3 為 2021——新樹無沿舊理由）。
6. **機密佔位值黑名單**：`.txt.example` 統一內容 `CHANGE-ME-placeholder`；server config 拒收
   `CHANGE-ME` 開頭值（boot panic 指名）——把 rev3 的「example 誤用防呆」從慣例升為機制。

## R4. 裁剪帶入邊界（ADR 0020 落實）

帶入改寫 9 項與不帶清單（含歸屬去處）詳 brainstorm §4——裁剪原則：rev3 功能刀產物
（013 CF 閘、M-9 limit_req、trust-model）與他刀資產（prod／acme／obs／metrics／cleanup-job）
一律不帶；帶入檔逐一改 rev4 語境（port 歸位、服務名、六 secrets、專案名）。
