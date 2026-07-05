# Data Model: 004-system-settings（形定稿）

本刀機器基準：後端 wire／型別 registry／授權／audit 結構（§1~§5）＋前端 typing／locale／
route 結構（§6）。權威鏈：constitution §I.3（wire 凍結）＋ADR 0026／0027／0028＞本檔；
資料層＝002 baseline（不動）。

## 1. 資料層（002 baseline、零改動）

- `system_settings` KV：PK `setting_key`(varchar64)、`setting_type`、`setting_value`、
  `description`＋審計六欄（變體 A）。8 seed（`single_session_default` enum:on,off／
  `password_min_length` number／`password_max_length` number／`password_require_*`×5 enum:on,off）。
- casbin policy（002 seed）：`R_SUPER` for `getSystemSettings`(GET)／`updateSystemSetting`(POST)。
- sys_menu：`manage_system-settings` 條目已 seed（供日後 dynamic 選單）。

## 2. wire 契約

- `GET /systemManage/getSystemSettings`（super-only）→ `Res<Vec<SettingItem>>`（不分頁 flat array）。
- `SettingItem`（`#[serde(rename_all="camelCase")]`）：`settingKey`／`settingValue`／
  **`settingType`**（★rev4 rename，非 rev3 `valueType`）／`description?`；審計欄不上 wire。
- `POST /systemManage/updateSystemSetting`（super-only）：req `UpdateReq{settingKey, settingValue}`
  → `Res<()>`（成功 `{data:null, code:"0000", msg:"common.success"}`）。
- 業務錯誤（Biz 2222、HTTP 200 信封）：`biz.systemSettings.notFound`（key 不存在、不新增）／
  `biz.systemSettings.invalidValue`（型驗失敗、不寫入）。授權失敗＝`5003`（system.forbidden、HTTP 403）。
- 新增 biz key＝13 碼 `2222` 的 `Biz(Cow<'static,str>)` 入參 key（error.rs 已支援、無需改碼表）。

## 3. 型別驗證 registry（ADR 0026）

- `validate(setting_type, value) -> Result<String, AppError>`（回正規化後值；錯→`Biz(invalidValue)`）：
  | type | 驗證 | 正規化落庫 |
  |---|---|---|
  | `number` | `parse::<i64>` 成功＋per-key 範圍內 | `n.to_string()`（canonical、棄空白/前導零/正號） |
  | `enum:a,b,…` | 值 ∈ `split(',')` 集合 | 原值（集合成員即 canonical） |
  | 其他（未知） | **fail-loud 拒**（B-051） | — |
- per-key number 範圍（const 表）：`password_min_length`→`1..=128`；`password_max_length`→`1..=256`
  （合理界；真實密碼策略約束由 auth 刀定）。範圍宣告落點＝const 資料（key→(min,max)）。

## 4. 授權骨架（ADR 0027）

- `Claims{uid:i64, sid, jti, roles:Vec<String>〔hint〕, iss, aud, exp, iat}`（`jsonwebtoken` HS256 decode）。
- `AppState{db:DatabaseConnection, jwt:JwtConfig, enforcer:Arc<RwLock<Enforcer>>, ...}`；
  handler 走 axum `State(state)`＋`Extension(claims)` extractor。（redis 熱套用 stub 欄可延後、R6。）
- `enforce_mw`（auth 骨架）：`bearer`(Authorization→`jwt::verify`→3333 fail-closed)→注入 Claims→next。
  ★本刀只 JWT-decode＋Claims 注入；session/denylist 屬 auth 刀。
- `require_policy(path,method)`（authz layer）：`roles_of_user(db,uid)` DB-fresh→`enforcer.enforce((role,path,method))`→deny→`PermissionDenied`(5003)；掛 `casbin_enforce_total` counter。
- route wiring：外 `enforce_mw`＋內 per-route `require_policy`；(path,method) 入覆蓋閘 registry。
- ★JWT `sign`／登入端點不在本刀（auth 刀）；測試注入 super Claims / 手工 test token。

## 5. 審計 op-log（§I.6；同 txn）

- `mutate_in_txn(conn, f)`：業務寫＋op-log 同 txn（`Some(AuditEvent)`→write+commit、Err 全 rollback）。
- `AuditEvent{operation:Update, entity_table:"system_settings", entity_id:None〔KV String-PK〕,
  payload_before/after:audit_json〔含 setting_key〕, operator, trace_id, ...}`。
- `update_by_key` 成對寫 `updated_at`／`updated_by`（§I.6）；`build_update_active_model` `now` 注入純測。
- ★本刀最小 audit 接地：operator=注入 uid；IP/trace 可簡化（無真登入流量、實作定最小形）。

## 6. 前端模型（base-web 首刀；★軌道＋Amendment (iv)）

- **typings**（ADAPT 新檔 `src/typings/api/rev4-system-settings.d.ts`）：declaration-merge
  `Api.SystemManage.SystemSetting{settingKey, settingValue, settingType, description?}`＋
  `UpdateSystemSettingReq{settingKey, settingValue}`（camelCase 對齊後端）。
- **service**（WRAPPER 新檔 `src/service/api/rev4-system-settings.ts`）：`fetchGetSystemSettings()`→
  `SystemSetting[]`；`fetchUpdateSystemSetting(key,value)`→`void`（直接路徑 import）。
- **page**（★(e) `views/manage/system-settings/index.vue`）：前綴分區（`password_*`→密碼策略／
  其餘→會話設定）；型別驅動控件（`enum:on,off`→`NSwitch`／`number`→`NInputNumber` per-key min/max／
  其他→text）；恆 refetch after submit。route 由 elegant-router 自動生成（`manage_system-settings`）。
- **i18n（★(i)~(iv)）**：
  - (i) 攔截器 `src/service/request/index.ts:71/109` msg→`$t`（backend 命名空間；不碰碼分組/retry）。
  - (ii) `backend` 命名空間（key＝`backend.<root>.<entity>.<condition>`）＋settings 頁 key
    （`page.manage.systemSettings.*`）。
  - (iii) `App.I18n.Schema` 加 `backend` 型＋`page.manage.systemSettings` 型。
  - (iv) **完整 zh-tw locale**：`langs/zh-tw.ts` 全字典（10 命名空間 ~515 鍵、對齊 zh-cn）＋
    6 inline 註冊（locale.ts/app.d.ts LangType/naive.ts/dayjs.ts/store localeOptions 加繁體/index.ts 預設 zh-TW）。
- **守門**（typecheck+lint、無 vitest）：locale 對等 lint（zh-tw/zh-cn/en-us 全字典鍵集一致）＋
  vue-tsc（LangType/Schema/RouteKey 型別閘門）＋lint；datetime formatter lint（§8）。
- **fork-delta**：所有 inline 改動走 `rev4-inline` 標記（修改型原行註解／新增型圈界）。
