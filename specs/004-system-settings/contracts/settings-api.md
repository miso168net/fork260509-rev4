# Contract: 系統設定 API＋型驗＋授權（004-system-settings）

後端行為契約（驗收比對規則；機器基準＝data-model.md §2~§5）。

## 1. GET /systemManage/getSystemSettings（super-only）

| 面向 | 契約 |
|---|---|
| 授權 | `enforce_mw`＋`require_policy(...,"GET")`；非 super→`5003`（HTTP 403 信封）；無 token→3333/擋下 |
| 回應 | `Res<Vec<SettingItem>>`——統一信封、`data`＝設定陣列（不分頁）、`code "0000"`、`msg "common.success"` |
| SettingItem | camelCase `{settingKey, settingValue, settingType, description?}`；審計欄不出現（出現＝FAIL）|
| 排序 | `ORDER BY setting_key`（穩定序）|
| 涵蓋 | 回全 8 seed 設定 |

## 2. POST /systemManage/updateSystemSetting（super-only）

| 面向 | 契約 |
|---|---|
| 授權 | 同上（POST）|
| req | `{settingKey, settingValue}`（camelCase）|
| 成功 | 值（正規化後）持久化＋同 txn op-log→`Res<()>`＝`{data:null, code:"0000", msg:"common.success"}` |
| notFound | key 不存在→`Biz` `2222` `biz.systemSettings.notFound`（HTTP 200 信封）、**不新增鍵**、不寫入 |
| invalidValue | 型驗失敗→`Biz` `2222` `biz.systemSettings.invalidValue`、**不寫入**、無 op-log |
| audit | 成功寫 `sys_operation_log`（Update、entity_table=system_settings、entity_id=null、before/after json 含 key）＋成對 updated_at/by |

## 3. 型別驗證（ADR 0026；純函式、單元測試）

- `number`：`parse` 成功＋per-key 範圍〔`password_min_length` 1..=128／`password_max_length` 1..=256〕→正規化 canonical 落庫；否則 invalidValue。
- `enum:a,b`：值 ∈ 集合；否則 invalidValue。
- 未知型（registry 無對應）：**fail-loud invalidValue**（絕不放行）。
- 負面測試：number 非數字/界外/前導零正規化；enum 非成員；未知型拒；notFound 不新增鍵。

## 4. 授權（ADR 0027；最小骨架＋測試身分）

- `require_policy`＝DB-fresh roles（`roles_of_user`、非 claims.roles）→casbin enforce（已 seed R_SUPER policy）→deny 5003。
- `enforce_mw`＝JWT decode（`jsonwebtoken` HS256、verify iss/aud/exp）→注入 Claims。JWT sign／登入留 auth 刀。
- 測試：注入 super Claims / 手工 test token（同 secret sign）＋R_SUPER user-role seed→super 過、非-super 5003。

## 5. 守門（測試即產品）

- settings 兩端點掛 contract case＋覆蓋閘（US3 registry 雙向；demo case 移除後對齊）。
- 型別 registry 單元測試（§3 負面全覆蓋）。
- facade op-log 同 txn 測試（成功落 op-log／invalidValue 不落／rollback）。
- authz 測試（super/非-super、注入身分）。
- **首建 `entity_access_lint`**：掃 handler 零 path-root `entity::`（走 facade）；沿 003 lint 形（源碼掃描或註冊表形，實作定）。
- 容器內 `cargo test --workspace` 全綠。
