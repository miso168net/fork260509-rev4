# Research: 004-system-settings

Phase 0 產出。決策面由 brainstorm（七題、2026-07-05）＋clarify（zh-tw 全字典）＋plan 實測
（前端 locale 機制／rev3 後端結構深接地、2026-07-05）解決。含一項 **Constitution Amendment**
（R7：zh-tw 全字典逾 ★I18N-WIRING (ii)→ADR 0028 立 (iv)、v1.1.0）。實測於 004 dev stack 完成。

## R1. rev3 後端結構受控參照（§I.5：結構參照、全新寫、零整檔拷貝）

- **facade**（`model/facade/system_settings.rs` 形）：`find_all<C: ConnectionTrait>`（`order_by_asc(SettingKey)`、無分頁無 soft-delete）／`find_by_key<C>`（`find_by_id`、miss→`Ok(None)`）／`update_by_key<C: TransactionTrait>`（走 `mutate_in_txn` 同 txn 落 op-log）。`build_update_active_model` 純測 seam（`now` 注入）：`Set` 三欄 `setting_value`／`updated_at`／`updated_by`、PK Unchanged。`AuditSerialize::audit_json` 逐欄 `serde_json::json!`、無遮蔽、`DateTimeWithTimeZone→to_rfc3339`。★facade 是 entity 存取唯一管道（`entity_access_lint` 豁免點）。
- **型別驗證**（handler 內純函式 `validate_value_type(value_type,value)->Result<(),AppError>`）：`number`（bare、無冒號）先判→`parse::<u32>`＋範圍；`enum:a,b`（`split_once(':')`）→集合成員；其他→保守放行〔rev4 改未知型拒、R3〕。錯誤＝`Biz("biz.systemSettings.invalidValue")`（2222）。
- **handler**：`get_system_settings`（`find_all`→`Vec<SettingItem>`→`Res::ok`、不分頁）／`update_setting`（`find_by_key`〔notFound→2222〕→`validate`→`ctx.to_audit_meta(uid)`→`update_by_key`〔+op-log〕→race guard→〔熱套用 stub〕→`Res::ok(null)`）。
- **授權 seam**（R4）＋**AppState**（R4）＋**audit op-log**（R5）詳下。

## R2. rust 依賴釘版（雙查紀律；資料源＝rev3 workspace 解析＋crates.io）

| 依賴 | 版本 | features／備註 |
|---|---|---|
| sea-orm | 1.1.20（workspace 現值） | `default-features=false`＋`["macros","sqlx-postgres","runtime-tokio-rustls"]`（無 time、走 chrono backend）；facade/entity/txn 用 |
| jsonwebtoken | 9（rev3 現值；plan 定完整三段〔9.3.x 最新 stable〕雙查後釘） | JWT decode（HS256）；★MSRV：拉 `time`→若 toolchain 1.96 需比對 `time`/`simple_asn1` lock 釘 |
| casbin | 2.20.0（workspace 現值） | `default-features=false`；enforcer |
| metrics | 0.23（rev3 現值） | `casbin_enforce_total` counter（enforce_role_path_method）——★須與 axum-prometheus recorder 同版 |
| redis | 0.27（rev3 現值） | ★本刀熱套用＝documented-stub（R6）、**不建 publish**→redis 依賴**可暫不加**（state.redis 欄留 stub、或整欄延後） |
| arc-swap | 1.9（rev3 server-only） | AppState 內若用 ArcSwap（ip_rules 等非本刀面、可不引） |

★釘版於 plan→tasks 間以 R2 完整三段版號定死；本刀新增面＝jsonwebtoken＋casbin＋metrics（sea-orm/serde 已在 003 workspace）。casbin adapter＝已 vendored `sea-orm-adapter`（002）。

## R3. 型別驗證 registry（ADR 0026 執行面；per-key 範圍定案）

- registry 形：`setting_type`→validator；波1 填 `number`／`enum`。
- **number**：`parse::<i64>`（或 u64）成功→canonical 正規化（`n.to_string()` 落庫、棄空白/前導零/正號）；範圍 **per-key 宣告**（棄 rev3 全域 1..=1024）：
  - `password_min_length`：`1..=128`；`password_max_length`：`1..=256`（合理界、防荒謬；真實密碼策略約束由消費 auth 刀定——本刀只防絕對無效值）。
- **enum:a,b**：集合成員。
- **未知型**（registry 無對應）：fail-loud `Biz(invalidValue)` 2222（棄 rev3 保守放行；B-051）。
- 落點：驗證 registry 住 handler 或獨立 `validation` 模組（實作定）；per-key 範圍表 const 資料。

## R4. 授權 seam（ADR 0027 執行面；最小骨架＋測試身分）

- **Claims**（`auth/jwt.rs`）：`{uid:i64, sid, jti, roles:Vec<String>〔hint、非授權源〕, iss, aud, exp, iat}`；`jsonwebtoken::decode` HS256、`Validation` set iss/aud、leeway 0。**本刀只做 decode／verify＋Claims 注入骨架；sign／登入端點留 auth 刀**。
- **enforce_mw**（auth、注入 Claims）：`bearer`(Authorization strip→verify→3333 fail-closed)→注入 Claims→next。★本刀 enforce_mw **僅 JWT-decode＋Claims 注入**（rev3 的 is_current 單session／denylist 屬 auth/session 刀、本刀不帶）。
- **require_policy(path,method)**（authz、per-route layer）：`roles_of_user(db,uid)` **DB-fresh**（忽略 claims.roles）→`enforce_role_path_method(enforcer,roles,path,method)`〔casbin enforce＋`casbin_enforce_total` counter〕→deny→`PermissionDenied`（5003）。
- **enforcer**：住 `AppState.enforcer: Arc<RwLock<Enforcer>>`；`init_enforcer(db)`＝`DefaultModel::from_str(MODEL_CONF 3-tuple RBAC)`＋`SeaOrmAdapter::new(db)`＋`load_policy`。
- **route wiring**（rev4 鏡像）：外層 `enforce_mw`（auth）＋內層 per-route `require_policy`（authz）；兩 (path,method) 亦入覆蓋閘 registry。
- **測試身分**：注入 super Claims（或同 secret `jwt::sign` 手工 test token）＋DB seed 的 R_SUPER user-role→驗 super 過／非-super 5003。

## R5. 審計 op-log（§I.6；同 txn；KV String-PK 處理）

- `mutate_in_txn<C:TransactionTrait,...>(conn, f)`：`begin`→`f(txn)` 回 `(txn, R, Option<AuditEvent>)`→`Some`→`sys_operation_log::write_in_txn`→`commit`（業務寫＋op-log 同 txn、Err 全 rollback）。
- `AuditEvent{operation:Update, entity_table:"system_settings", entity_id:None, payload_before/after:audit_json, operator, xff, ip_confidence, trace_id}`。**KV String-PK：`entity_id=None`、`setting_key` 進 payload json**（rev4 必複製此形）。
- `AuditMeta` 由 `RequestContext::to_audit_meta(uid)` 產（operator IP／trace）。★`RequestContext`／audit_ctx 是 007 面——本刀需最小接地（trace/IP 可先簡化：本刀無登入真流量、op-log 記 operator=注入 uid、IP 可 None/localhost，實作定最小形）。

## R6. 熱套用 documented-stub（B-023 定形留空）

- `update_setting` commit 後留**接點註記/stub**（頻道 `settings:invalidate`、訊息＝key、fail-open 語意的文件化定形）、**不建 publish**、**redis 依賴可不加**。首個快取消費者刀（auth 密碼策略／session）進場時補 publish＋subscribe＋redis。設定讀恆即時打 DB（無快取）。

## R7. 前端 locale 機制（實測；★Amendment ADR 0028）

- **實測：soybean locale 非資料驅動、需 inline 手動註冊**。加完整 zh-tw＝`langs/zh-tw.ts` 新檔（~515 鍵、對齊 zh-cn）＋6 處改既有 inline：`locale.ts`（import+map）、`app.d.ts` `LangType` union 加 `'zh-TW'`、`naive.ts`（naiveLocales+naiveDateLocales，naive-ui 有 `zhTW`/`dateZhTW`）、`dayjs.ts`（import+localMap）、`store/app` `localeOptions` 加「繁體中文」、`index.ts`／app store 預設 `'zh-CN'`→`'zh-TW'`。
- ★逾 ★I18N-WIRING (ii)→**ADR 0028 立 (iv)、constitution v1.1.0**（已 commit）。
- **型別閘門**（typecheck 把關）：`locale.ts`/`naive.ts`/`dayjs.ts` 用 `Record<LangType,X>`→加 `'zh-TW'` 後三 map 漏補即 vue-tsc 紅；`App.I18n.Schema`（`Record<LangType,Schema>`）→漏鍵/漏語言紅；`RouteKey` union→route locale map 漏補紅。★`localeOptions` 是純陣列、**不受型別強制**（語言選單漏加不會紅、須人記）。
- **無測試框架**（實測：無 vitest/@vue/test-utils）→前端驗收＝**vue-tsc typecheck＋lint**（user 拍板 B；不引 vitest）。

## R8. i18n msg→$t 接線（★(i)；實測落點）

- 接線點＝`src/service/request/index.ts:71`（modal content）＋`:109`（onError message）——現原文顯示 wire `msg`；本刀改為經 `$t` 譯（backend 命名空間）。**不碰** L55/62/88 的碼分組（logout/modalLogout/expiredToken）與 retry 控制流。
- backend 命名空間 key 形＝`backend.<root>.<entity>.<condition>`（§III(ii)）；wire `msg`（如 `biz.systemSettings.invalidValue`／`system.forbidden`／`common.success`）映射到 `backend.*` 譯文；映射細節（前綴策略）於 tasks 定。

## R9. 路由/選單（實測）＋B-009 facade 樣板碼審

- **route**：elegant-router 自動生成（建 `views/manage/system-settings/index.vue`→`pnpm gen-route`→自動出 `manage_system-settings` route＋`RouteKey`＋route locale 型強制）。★施工需實測 regen 是否保留手填 meta（roles/icon/order）。
- **選單**：現 static 模式（`.env VITE_AUTH_ROUTE_MODE=static`）、route 驅動＋roles meta 過濾；super-only settings 頁仍需 super 身分過濾器放行（拍板 7 live 限制成立）。★本刀維持 static（dynamic 需 getUserRoutes＝auth 刀）；sys_menu `manage_system-settings` 已 seed（002、供日後 dynamic）。
- **B-009**（RI hybrid 分層重審、承 003 拍板 4）：rev3 facade→handler→error 形樣板碼代價實審——結論：**沿用單一映射來源骨架**（AppError 單一來源、facade 收 entity 存取、handler 零 entity::）＝低樣板、可讀；per-method 一 error enum 案**不採**（system-settings 只兩端點、Biz(Cow) 已足；未來 CRUD 密集刀再評）。B-009 收刀刪列。

## R10. demo 端點刪除（B-056）

- 刪：`handler/demo.rs`＋`handler/mod.rs` 掛載＋`router.rs` ROUTES /demo-wire 條目與 in-module demo 測試＋`tests/contract.rs` demo-wire ContractCase 與 `len==2` 斷言（改對齊新端點數）＋demo-wire 的 offset 守門 case（改掛到真 settings 端點的時間欄若有／或移除）。移除後覆蓋閘/契約守門重跑全綠。
