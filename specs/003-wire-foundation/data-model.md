# Data Model: 003-wire-foundation（wire 形定稿）

本檔＝本刀機器基準：13 碼矩陣總表（§1＝table-driven contract test 的對照源）、信封
與序列化形（§2）、快照與註冊表結構（§3~§4）、demo 端點形（§5）。權威鏈：
constitution §I.3（凍結）＞本檔（執行面轉錄）；不一致以 constitution 為準並回報。

## 1. 13 碼矩陣總表（contract test 機器基準）

| code | 語意 | i18n key（wire msg） | HTTP | 可發性 | 錯誤型變體 |
|---|---|---|---|---|---|
| 0000 | 成功 | common.success | 200 | 可發 | Success（通常走 Res::ok、變體供矩陣完整性） |
| 1000 | 登入失敗 | auth.login.failed | 200 | 可發 | LoginFailed |
| 2222 | 業務驗證錯誤 | 入參 key（biz.* 慣例、未指定傳 biz.error） | 200 | 可發 | Biz(key) |
| 3333 | token 過期 | auth.token.expired | 200 | 可發 | TokenExpired |
| 7777 | 他處登入（前端 modal） | auth.session.kicked | 200 | 可發 | ModalLogout |
| 7778 | 保留 | — | — | **不可發（無變體）** | — |
| 8888 | 請重新登入（靜默登出） | auth.session.reLogin | 200 | 可發 | Logout |
| 8889 | 保留 | — | — | **不可發（無變體）** | — |
| 9998 | 保留 | — | — | **不可發（無變體）** | — |
| 9999 | 保留 | — | — | **不可發（無變體）** | — |
| 4040 | 找不到（router fallback） | system.notFound | **404** | 可發 | NotFound |
| 5003 | 無權限 | system.forbidden | **403** | 可發 | PermissionDenied |
| 5000 | 內部錯誤 | system.internal | 200 | 可發 | Internal |

- 可發碼恰 9、保留碼恰 4；HTTP 例外恰 2（4040→404、5003→403）、其餘一律 200。
- key 值照 rev3 已驗證形逐字（受控參照）；新需求優先 reuse 既有碼、新碼＝動凍結面
  走 Amendment（ADR 0004）。

## 2. 信封與序列化形

- `Res<T>`：`{data, code, msg}`——欄序＝宣告序（data→code→msg）；`code` string；
  錯誤時 `data: null` **不省略**；無 `success` bool；預設 HTTP 200。
- `PageRes<T>`：`{current, size, total, records}`（camelCase）；空頁 `records: []`
  （非 null）；無 `pages`／`success`。
- 時間欄：一律 ISO-8601／RFC3339 **帶時區偏移**（實形由 contract case 凍結）。
- id 序列化：typings 宣告 string 的 id 欄→JSON string（i64 源、邊界轉字串）；宣告
  number 的欄→JSON number、前置 2^53 守衛（超限 fail-loud、絕不靜默失真）；型別
  謊言帳本歸零起算（顯式偏離＝拍板立 ADR）。

## 3. wire-schema 快照結構

- 檔位：`rust-api/server/tests/fixtures/wire-schema.json`（追蹤；tools/wire-schema
  extract 寫入、原子替換）。
- 形：JSON Schema draft-07；`definitions` 鍵＝完整限定名（如
  `Api.Common.PaginatingQueryRecord`、`Api.SystemManage.Menu`）。
- 來源檔集：base-web `src/typings/common.d.ts`＋`src/typings/api/*.d.ts`（四檔）；
  基準值（2026-07-04 實測）＝35 definitions、其中 26 個 `Api.*` 型。
- 無產生時點欄位；同源重抽 byte 級一致（新鮮度證據形＝重抽 diff 空）。

## 4. route 註冊表與 contract case registry

- 註冊表（router 模組內 const 資料）：每條 route＝`{path, method, handler 對應,
  case 鍵, 信封例外標記}`；axum Router 由註冊表生成——單一來源實體化。
- 本刀註冊表內容：`GET /health`（例外標記＝plain text）＋`GET /demo-wire`（信封；
  後端形——001 路由契約：front-nginx strip `/api` 前綴、後端 route 不帶 `/api`，
  對外形＝`/api/demo-wire`）；`/metrics` 不入表（endpoint 歸 obs 刀、例外規則入
  13 碼常量註記）。
- contract case registry（測試側）：case 鍵 → 驗證函式；覆蓋閘迭代註冊表逐條斷言
  registry 含其 case 鍵、缺即紅指名。

## 5. demo 驗證端點形（暫時物）

- `GET /demo-wire`（對外 `/api/demo-wire`）→ `Res<DemoData>`；`DemoData`＝
  `{id: string（i64 源轉字串）, name: string, createdAt: RFC3339 帶 offset}`；
  msg＝`common.success`。
- 生命週期：本刀收刀時登記待辦、首個功能刀執行刪除（連同其 case 與註冊表條目）。
