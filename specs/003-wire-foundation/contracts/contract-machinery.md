# Contract: 契約機器化管線（003-wire-foundation；ADR 0025 執行面）

抽取命令／裁判消費／覆蓋閘的行為契約。快照結構機器基準＝data-model.md §3~§4。

## 1. `tools/wire-schema extract`（需 stack 在）

- 行為：base-web 容器內（`/app` cwd）以 npx 釘版執行
  `typescript-json-schema@0.67.4 "src/typings/{common,api/*}.d.ts" "*"
  --ignoreErrors --required` → 確定性輸出寫
  `rust-api/server/tests/fixtures/wire-schema.json`（原子替換、絕不寫部分結果）。
- 唯讀鐵則：不碰 base-web 工作樹、package.json、pnpm lock（npx 一次性、裝進容器
  npm cache）；前端 porcelain 前後皆空。
- 失敗語意：stack 不在→非零退出＋提示啟動命令；抽取工具非零退出→透傳失敗、不寫檔。
- 確定性：同 typings 重跑 byte 級一致（無時點欄位）——「再抽 diff 空」＝新鮮度證據
  （同 002 快照紀律）。
- 新鮮度：動 typings／加 route 的刀必重抽並隨該 commit（守門句隨本刀入活書 §8）。

## 2. contract test 裁判消費（離線、住 server/tests/）

- 讀 fixtures/wire-schema.json（快照缺失＝測試紅、fail-loud 指名補救命令）。
- 本刀受審面（clarify Q1）：信封／分頁**通用形**——以 `Api.Common.*` 通用型驗
  `PageRes` 等序列化輸出＋裁判機制自測（schema 解析、驗證器行為）；per-route
  業務型受審自波 1 起（機制就位、消費者後到）。
- 驗證器＝jsonschema 0.46.9（dev-dependency）；draft-07。

## 3. 覆蓋閘（cargo test 形；ADR 0025）

- 比對語意：迭代 router 註冊表（單一來源 const 資料）逐條斷言 contract case
  registry 含其 case 鍵；缺＝紅＋指名路由；多餘 case（registry 有、註冊表無）＝
  紅＋指名（防殭屍 case）。
- 信封例外端點不豁免：`/health` 必有 case、驗 plain text 例外形。
- 不進 pre-commit（需編譯與測試環境；FR-009 分工——與 002 三閘同定位）。

## 4. 三類守門 case 契約（ADR 0004 執行面）

1. 13 碼 table-driven：測試側常量表與 data-model §1 逐列對齊（表長恰 13）；可發碼
   逐碼驗 HTTP status＋信封形。
2. 保留碼永不發出：編譯期（無變體）＋列舉完整性（可發碼集合恰 9）。
3. 時間欄 offset：demo 響應實測、無 offset＝紅。
