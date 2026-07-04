# 003-wire-foundation 刀 brainstorm — 統一信封＋13 碼守門＋契約機器化骨架

波 0 第三刀（最後一刀）。上游輸入凍結：wave-0-plan §2.3（交付物七項全數承接）、
constitution §I.3（13 碼矩陣／信封形／id 序列化／msg=key／契約機器化——全數凍結、
本刀只做執行面）、ADR 0004（三類守門執行面）、活書 §8 錯誤碼與 datetime 兩列
「隨 wire 地基刀建立」義務。rev3 實作接地（唯讀參照、§I.5 紀律下全新寫）：
server/src/envelope.rs（134 行）＋error.rs（304 行）＋tests/endpoint_coverage_lint.rs。

## 0. 拍板紀錄（2026-07-04、四題）

| # | 題 | 拍板 | 要點 |
|---|---|---|---|
| 1 | 信封／錯誤型住哪 | **server 內模組**（envelope.rs＋error.rs、沿 rev3 已驗證形） | AppError 的 IntoResponse 綁 axum、放 server 最自然；目前零第二消費者、抽 crate 屬 YAGNI；日後真有 job/cli 再抽＝機械搬移 |
| 2 | typings→JSON Schema 裁判載體 | **快照管線形**（沿 002 前例） | 顯式抽取命令（需 stack）於 base-web 容器內 npx 釘版執行、唯讀 typings；產物＝追蹤快照；contract test 離線消費；pre-commit 維持離線秒級 |
| 3 | coverage gate 落點 | **cargo test 形**（沿 rev3） | rust 端讀 rust 源頭最不脆弱；與三類守門同一驗證入口；python 解析 rust＝L-052 類脆弱形、且 reference/routes 維持 stub 屬波 0 出口預期 |
| 4 | B-009（RI hybrid 分層重審）處置 | **遞延至首個帶 facade 的功能刀**＋收刀改觸發字樣 | 003 零 facade 零業務方法、樣板碼代價無實體可審；本刀只落映射單一來源骨架、不預決 per-method enum 案 |

ADR：拍板 2＋3 立 **ADR 0025**（wire 契約機器化執行面；draft、隨本檔定案轉 accepted）；
拍板 1＋4 屬工程選擇、本節即記錄。

## 1. server 內模組（信封＋錯誤型）

- `server/src/envelope.rs`：`Res<T>{data,code,msg}`——欄序固定（宣告序）、`code` 為
  string、錯誤時 `data:null` 不省略、無 `success` bool、預設 IntoResponse→HTTP 200；
  `PageRes<T>{current,size,total,records}`（camelCase、空頁 `records:[]`、無 `pages`）。
- id 序列化＝逐欄位忠實 typings（§I.3）：宣告 string 的 id 欄於序列化邊界轉字串、
  serializer 帶 2^53 fail-loud 守衛；型別謊言帳本歸零起算（顯式偏離＝拍板立 ADR）。
- `server/src/error.rs`：`AppError` enum＝錯誤型→碼映射**唯一來源**——9 個可發碼有
  變體、4 保留碼（7778/8889/9998/9999）**刻意無變體＝編譯期不可構造**（rev3 驗證形、
  比 runtime 斷言強）；碼／key／http 烤進變體（HTTP 例外僅 4040→404、5003→403）；
  IntoResponse 建錯誤信封。`From<DbErr>` 不在本刀（首個產 DbErr 的刀帶入、沿 rev3 同判）。
- msg=i18n key：去前綴語意 key 形（如 `auth.login.failed`、`common.success`——rev3 形）；
  前端字典 `backend.*` 命名空間接線歸首功能刀（★軌道 (i)~(iii)、本刀零 base-web 改動）。
- router 模組＝route 註冊單一來源（coverage gate 掃描對象）；`/health` 維持 plain text；
  `/metrics` 例外入規則註記與測試、endpoint 本身歸 obs 刀。

## 2. 契約機器化管線（wire-schema 快照）

- 外層新工具 `tools/wire-schema`（python3 標準庫）：`extract` 子命令＝
  `docker compose … exec -T base-web npx -y <產生器>@<釘版>` 對 base-web
  `src/typings/api/` 四檔抽 JSON Schema（唯讀、不碰 package.json、零 fork 改動）；
  確定性排序、原子替換、無產生時點欄位（同 002 快照材質慣例）。
- 產物住**消費者旁**：rust-api worktree `server/tests/fixtures/wire-schema.json`
  （容器只掛 rust-api、外層 docs 掛不進去；test fixture 隨 worktree commit、兩段式
  commit 紀律照舊）。與 002「reference-src 住外層」不衝突——那是 docs-sync 的來源、
  這是 cargo test 的 fixture。
- 產生器工具與版本＝SDD research 必答：首選 ts-json-schema-generator，須先驗對
  `declare namespace Api` 環境宣告型 .d.ts 的可行性；備選 typescript-json-schema／
  tsc 自寫抽取腳本；釘完整數字版（npm 官方最新 stable、雙查後凍結於 spec）。

## 3. 三類守門＋coverage gate（全住 server/tests/）

1. 13 碼 table-driven contract test：每碼一組 case、整表覆蓋（HTTP status＋信封形狀）。
2. 保留碼永不發出：型別層無變體（編譯期）＋矩陣列舉測完整性（防變體被誤加回）。
3. 時間欄必 ISO-8601 帶 offset 斷言（demo 端點響應實測）。
- coverage gate：守門 test 比對 router 註冊單一來源 vs contract case registry——
  「每條 route 必有 contract case」、缺即紅；不入 pre-commit（閘門類需環境、FR-014 分工）。

## 4. demo 驗證端點

- 路徑走 `/api/` 前綴（§II #3）、名稱實作時定；回帶時間欄（timestamptz→ISO-8601 帶
  offset）＋string-id 欄假資料；分頁形 `PageRes` 由 contract test 直驗序列化、不必
  demo 承載。錯誤形由 router fallback（4040→404）＋contract test 覆蓋、demo 不另做
  錯誤參數。功能刀進場後可刪（收刀條件記入該刀）。

## 5. 驗收與收尾

- 驗收（wave-0-plan §2.3＋波 0 出口第 3 組）：容器內 cargo test 全綠（三類守門＋
  coverage gate 在內）；curl demo 端點驗信封實形＋msg 是 key＋offset 在場；
  curl /health 仍 plain text；lint 全綠。
- 收刀：活書 §8 錯誤碼與 datetime 兩列守門轉已就位＋新增 wire-schema 快照新鮮度句
  （動 typings／加 route 的刀必重抽並隨 commit）＋§4/§5 敘事對齊；ADR 0025 轉
  accepted 生效確認；**收 003 時波 0 出口六組檢查表整波重跑**、全綠才宣告波 0 收口。

## 6. 衍生處置判定

- B-009：遞延（拍板 4）；收刀時觸發字樣改「首個帶 facade 的功能刀 brainstorm」。
- B-001（routes extractor）：不入本刀（波 0 出口明文預期 routes 維持 stub）；收刀時
  觸發字樣改「首個**業務**路由落地時」——demo 屬暫時物、避免字面命中懸置。
- B-047（protected-reject detail 插值）：不入本刀——屬 casbin 治理域行為、本刀 msg=key
  純骨架無 protected 語意；觸發條件維持不動。

## 7. SDD 接續

user 手動起手 `/speckit-specify`（input＝本檔）→ clarify → plan（constitution §IV
九題對照；第 4 題 wire 對齊＝本刀主體）→ tasks → analyze；TDD 編排照 CLAUDE.md §2
模板 v2（防呆五件套＋看門狗）。
