# 004-system-settings 刀 brainstorm — 系統設定縱切（首個 facade/授權層＋base-web 首刀）

波 1 第一功能刀＋base-web 首刀。上游輸入：ADR 0008（縱切第一刀＝系統設定、最輕打樣、
骨架先定形）、B-023（系統設定域骨架：型別驗證／熱套用／UI 分區定形留空）、B-051（值型
驗證健壯化：未知型拒收＋number 正規形落庫）、constitution §III（★MODAL-WIRING (e)／
★I18N-WIRING (i)~(iii)／ADAPT／WRAPPER 軌道授權）＋§I.2／§I.3／§I.6。資料面已 baseline
（002：`system_settings` KV 表＋8 seed＋casbin R_SUPER policy）。rev3 實作接地（唯讀受控
參照、§I.5 全新寫）：`handler/system_settings.rs`＋`model/facade/system_settings.rs`＋
前端 rev3-* KV 頁（住 rev3-admin-base-web 分支、非上游）。

## 0. 拍板紀錄（2026-07-05、七題）

| # | 題 | 拍板 | 要點 |
|---|---|---|---|
| 1 | 範圍 | **全縱切（含前端）＝base-web 首刀** | facade→handler→授權→wire→前端 一次打通＋首啟 ★i18n 軌道與 base-web 守門；ADR 0008 原意、blast radius 最小 |
| 2 | 值型驗證骨架 | **型別 registry＋per-key 可宣告範圍** | 每型一 validator；number 正規化落庫＋per-key 範圍（棄 rev3 全域 1..=1024）；未知型 fail-loud 拒收（B-051）→ **ADR 0026** |
| 3 | settings 頁 vs ★(e) | **算 (e) 授權內（設定表單＝標準 manage 頁）** | KV 表單用標準 naive-ui 控件、非 bespoke 儀表板佈局；(e) provenance 本含 rev3 設定頁；spec 記授權依據、不 bump constitution |
| 4 | 授權層（登入另一刀） | **最小授權骨架＋測試身分** | require_policy（casbin enforce 已 seed policy→5003）＋enforce_mw 骨架（JWT decode 接點）；JWT 簽發/登入留 auth 刀；測試注入 super Claims → **ADR 0027** |
| 5 | 熱套用 | **documented-stub（不建 publish）** | handler 留熱套用接點註記/stub；首個快取消費者（auth/user-center 刀）進場時補 publish＋subscribe；現零消費者＝YAGNI |
| 6 | ADR 立案 | **0026＋0027 兩個都立** | 皆跨刀被引用的基礎模式；憲法 (e) 授權依據入 spec（非 ADR） |
| 7 | 前端 live 驗證 | **接受限制（碼+build+契約+單元/服務層）** | 動態路由需 auth；瀏覽器 login-gated 走查（登入→動態路由→頁面→改值）留 auth 刀；不建丟棄式 dev 旁路 |

ADR：拍板 2 立 **ADR 0026**、拍板 4 立 **ADR 0027**（皆 draft、隨本檔定案轉 accepted）；
其餘屬工程/範圍選擇、本節即紀錄。

## 1. 資料面（零 migration）

- `system_settings` KV 表（PK=`setting_key` varchar64 無序列、`setting_type`、`setting_value`、
  `description`＋審計六欄〔變體 A〕）＋8 seed＋casbin R_SUPER policy 皆已 baseline（002）。
  **本刀零 migration／零 seed 改動**。
- 8 key：`single_session_default`(enum:on,off)、`password_min_length`(number)、
  `password_max_length`(number)、`password_require_{uppercase,lowercase,digit,special,forbid_username}`(enum:on,off)。
- ★rev4 schema 差異：`value_type` 已改名 **`setting_type`**（002 定稿）→ wire 對外 **`settingType`**（非 rev3 `valueType`）；欄序審計欄在前、業務欄置尾。

## 2. 後端分層（首建 facade/model/auth/handler；rev3 結構參照、全新寫）

- **model/facade/system_settings.rs**（首個 facade＝entity 存取唯一管道）：`find_all`
  （ORDER BY setting_key）／`find_by_key`／`update_by_key`（`mutate_in_txn` 同 txn 落 op-log）。
- **model/audit**（首建 op-log seam）：`Update`＋entity_table＋before/after json；KV 的
  `entity_id=None`、key 進 payload；成對寫 `updated_at`/`updated_by`（§I.6）。
- **auth/**（首建授權骨架、最小——見 §4／ADR 0027）。
- **validation（型別 registry）**（ADR 0026）：per-type validator＋per-key 可宣告範圍；
  `number`→parse→canonical 正規化落庫＋per-key 範圍；`enum:a,b`→集合；未知型 fail-loud 2222。
- **handler/system_settings.rs**：`get_system_settings`（super-only、`find_all`→
  `Res::ok(array)`、**不分頁**）／`update_setting`（`{settingKey,settingValue}`→`find_by_key`
  〔查無→2222 不新增鍵〕→型驗→normalize→`update_by_key`〔+op-log〕→熱套用 stub 接點→
  `Res::ok(null)`）。
- **router.rs**：加 2 端點＋case key（掛 US3 覆蓋閘）；**刪 demo 端點（B-056）**。

## 3. wire 契約（快照重抽）

- `GET /systemManage/getSystemSettings` → `Res<Vec<SettingItem>>`；`SettingItem`（camelCase）：
  `settingKey / settingValue / settingType / description?`（審計欄不上 wire）。
- `POST /systemManage/updateSystemSetting`：req `{settingKey, settingValue}` → `Res<()>`
  （成功 data:null）；錯誤 2222 `biz.systemSettings.notFound`／`.invalidValue`（新增 biz key，
  循 13 碼 2222 Biz(key)）。
- typings 新增 → **wire-schema 快照重抽**（`python3 tools/wire-schema extract`、§8 新鮮度守門）。

## 4. 授權骨架＋熱套用 stub（B-023 定形留空）

- 授權（最小 seam，ADR 0027）：`require_policy(path,method)`（DB-fresh roles→casbin enforce
  已 seed policy→5003）＋`enforce_mw` 骨架（JWT decode→Claims 接點；**簽發/登入留 auth 刀**）；
  測試注入 super Claims／手工 test token 驗（super 過、非 super 5003）。
- 熱套用（**documented-stub**）：`update_setting` commit 後留接點註記/stub（頻道
  `settings:invalidate`、訊息＝key、fail-open 語意的**定形**），**不建 publish**；首個快取
  消費者（auth/user-center 刀）進場時補 publish＋subscribe。設定的讀恆即時打 DB（無快取要刷）。

## 5. 前端（base-web 首刀；★軌道＋ADAPT＋WRAPPER，全走 `rev4-inline` fork-delta 紀律）

- **ADAPT**（免授權）：`src/typings/api/rev4-system-settings.d.ts`（declaration-merge
  `Api.SystemManage.SystemSetting {settingKey, settingValue, settingType, description?}`＋UpdateReq）。
- **WRAPPER**（免授權）：`src/service/api/rev4-system-settings.ts`（`fetchGetSystemSettings`／
  `fetchUpdateSystemSetting`、直接路徑 import 避 barrel stale）。
- **★MODAL-WIRING (e)**：`views/manage/system-settings/index.vue`——KV 頁、前綴分區
  （`password_*`→密碼策略區／其餘→會話設定區、沿 rev3）、型別驅動控件（`enum:on,off`→NSwitch／
  `number`→NInputNumber〔per-key min/max〕／其他→text）、恆 refetch after submit；＋route／menu。
- **★I18N-WIRING (i)~(iii)**：(i) `src/service/request/` msg→`$t` 翻譯接線（不改控制流語意）；
  (ii) `src/locales/langs/*` 加 top-level `backend` 命名空間（`backend.<root>.<entity>.<condition>`）
  ＋譯文、**zh-TW 首發字典建置**；(iii) `App.I18n.Schema` 擴 `backend` 型。

## 6. 守門與測試（測試即產品）

- 後端：settings 端點掛 contract case＋US3 覆蓋閘；型別 registry 單元測試（normalize/範圍/
  enum/未知型拒）；facade op-log 同 txn 測試；authz 測試（super 過／非 super 5003、注入 Claims）；
  **首建 entity_access_lint**（handler 零 path-root `entity::`、走 facade）。
- 前端：**locale 對等 lint**（zh-tw/zh-cn 鍵集一致——§8「隨 base-web 首刀建立」守門）＋i18n
  typed Schema（加鍵漏語言 typecheck 紅）＋**datetime formatter lint**（§8 datetime 後半守門，
  base-web 首刀建立）。

## 7. 前端 live 驗證限制（拍板 7）

rev4 動態路由（`getUserRoutes` 是 auth 端點）＝無登入無法在瀏覽器點進 settings 頁。前端這刀
達成＝typings match wire＋vite build/type-check 綠＋頁面元件單元測試＋服務層整合測試（注入
test token 直打 live 後端驗 service↔wire）。瀏覽器 login-gated 走查留 auth 刀。

## 8. 明確不在本刀

真登入/JWT 簽發（auth 刀，B-008 未拍）｜熱套用 subscriber（首個快取消費者刀）｜其他業務
設定項｜demo 端點於本刀 router 面刪除（B-056、暫時物清償）。

## 9. 衍生處置判定

- **B-023 消化**：型別驗證（registry、ADR 0026）＋熱套用（documented-stub）＋UI 分區（前綴分區）
  三者定形落地／留空，B-023 收刀刪列。
- **B-051 消化**：值型驗證健壯化落入 ADR 0026，收刀刪列。
- **B-009**（RI hybrid 分層重審）：本刀是「首個帶 facade 的功能刀」＝其觸發點；brainstorm 期間
  就 facade 樣板碼代價實地審——沿 003 拍板 4「遞延至首個帶 facade 的功能刀」，本刀 plan 階段
  併審、結論入 spec（沿用單一映射來源骨架、per-method enum 案是否採由實作實據定）。
- 新衍生：base-web 首刀基建（i18n 軌道／locale lint／formatter lint／entity_access_lint）
  之未盡項隨實作 append BACKLOG。

## 10. SDD 接續

本檔定案後**手動**起手 `/speckit-specify`（input＝本檔）；specify 不在 brainstorm 流程內
自動觸發（否則 feature-branch pre-hook 不跑、spec 落在 default）。續 clarify→plan→tasks→analyze，
每步 commit；plan 階段做 rev3 受控參照接地＋B-009 facade 樣板碼審＋前端技術實測（vitest 是否
就位、i18n/路由結構）。
