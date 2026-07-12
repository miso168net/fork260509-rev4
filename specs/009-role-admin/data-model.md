# Data Model: 009-role-admin

**Branch**: `009-role-admin` | **Date**: 2026-07-12 | **Plan**: [plan.md](./plan.md)

schema 全於 002 凍結基線（出處＝`docs/generated/reference/schema.md` 實庫快照）。**唯一結構變更＝m007 加 `sys_casbin_policy_archive.role_id`**。本檔記實體、m007、狀態機三危險面、與載重不變式。

## 實體（皆凍結基線、除 m007 一欄外零變更）

### sys_role（角色）
六審計欄＋`status smallint`＋`role_code`／`role_name`／`role_memo text`／`role_home varchar`／`role_desc varchar`。partial-uniq `sys_role_code_active_uniq (role_code) WHERE deleted_at IS NULL`。
- **活性**＝`deleted_at IS NULL`；**啟用**＝`status = 1`（`2`＝停用）。
- **role_code**：不可變（FR-006）；形制守門 `^[A-Za-z0-9_]{1,64}$`（R8、addRole 單點把關；DB 欄本身無長度/字元約束）。
- seed 三角色：R_SUPER(1)／R_ADMIN(2)／R_USER_COMMON(3)，`role_home='home'`、`status=1`。

### sys_user_role（使用者-角色指派）
PK`(user_id, role_id)`、雙向 FK **RESTRICT**。本刀**唯讀消費**（deleteRole in-use 守門 count、掛載人數 userCount），不提供指派寫入（→ user 頁刀 B-064 族）。

### casbin_rule（現役授權，11 欄）
`id`／`ptype`／`v0..v5`（各 varchar(125)、v3/v4/v5 default `''`）／`protected bool NOT NULL default false`／`created_at`／`created_by`。uniq `(ptype,v0..v5)`＝policy 身分鍵。
- 本刀全 `ptype='p'`（zero g-rows；user→role 走 sys_user_role）。
- 三維語意：v0＝role_code；v1＝object（menu route_name／button code／endpoint path）；v2＝act（`menu`／`button`／`GET`／`POST`／`DELETE`）。
- **v0..v5 存為六獨立欄、無逗號串接** → role_code 無字串拼接注入面（R8）。
- seed 149 列全 `p` 型；19 列 protected=true 全 v0=R_SUPER（治理面恢復路徑）。

### sys_casbin_policy_archive（授權歸檔，13 欄 → m007 後 14 欄）
`id`／`created_at`（可空、原 policy 審計快照）／`created_by`／`archived_at`（default CURRENT_TIMESTAMP）／`archived_by`／`archive_reason varchar(32)`／`ptype`／`v0..v5`（v3/v4/v5 default `''`）**＋m007 `role_id bigint NULL`**。索引 `idx_casbin_archive_role_dim (v0,v2)`。
- **對照 casbin_rule 11 欄，唯一缺欄＝`protected`**（id 為代理鍵不計）。**對 restore 完整性影響＝零**——見下「快照完整性不變式」。
- `archive_reason`：撤銷類 distinct 值（menu_revoke／button_revoke／endpoint_revoke 類）｜`role_soft_delete`。**維度由 v2 推導**（menu/button→原值、其餘→endpoint），不新增維度欄。

### sys_menu（選單登記，唯讀消費）
含 `buttons jsonb`／`i18n_key`／route_name partial-uniq。menu 維候選（樹）＋button 維候選（buttons jsonb 聯集去重）＋menu id↔route_name 映射的真源。

## m007 migration（唯一結構變更）

```
up:   ALTER TABLE sys_casbin_policy_archive ADD COLUMN role_id bigint NULL;
down: ALTER TABLE sys_casbin_policy_archive DROP COLUMN role_id;
```
- 型別 `bigint`（對齊 sys_role.id）、nullable、**不設 FK**（歸檔列壽命長於角色列、FR-040）、**無 DEFAULT**（NULL＝「歷史列未知」語意）、**不加索引**（治理表量級小、seq scan 足；主查詢由既有 `idx_casbin_archive_role_dim` 覆蓋）。
- 走 gate1 STRUCTURAL_ADDITIVE_ALLOWLIST（schema-gate 一條）、白名單同 commit（L-109）。
- 本刀後所有 `insert_archived`（revoke 與 role_soft_delete 兩路）一律填 role_id；歷史列自然 NULL → FR-029 判不可復原（誠實退化）。

## 狀態機三危險面

### 1. 角色生命週期（US1）
```
（無）─addRole─▶ 啟用(status=1) ◀─updateRole status─▶ 停用(status=2)
                    │                                      │（停用即斷權：roles_of_user 濾掉）
                    └─────────deleteRole（三層守門過門）────┴──▶ 軟刪(deleted_at set)
                                                              ＋同交易 archive_all（全維含 protected、reason=role_soft_delete）
軟刪為單向終態：無 role restore（FR-012）；code 可經 partial-uniq 重用、新角色零授權起步、不繼承（歸檔＋同實例判定雙封）
```
deleteRole 三層守門（鎖內重判、序固定）：①seeded hardcode → ②in-use（txn 內 count sys_user_role、拒因帶 userCount）→ ③self-role。batchDelete 自管 txn、逐項驗證整批拒 no-partial（B-049）。

### 2. 授權治理狀態機（US2、全量替換）
```
desired 全集 ─▶ 讀 current（鎖內）─▶ diff{to_revoke, to_grant}
   │
   ├─ to_revoke 含 protected=true ─▶ Rejected（任何寫之前、零變更、2222 protectedRevoke＋data 明細）
   └─ 否則 ─▶ archive-move（INSERT archive 帶 role_id、reason 撤銷類 → DELETE live）
              ＋grant INSERT（protected=false、created_at/by 補寫）
              ＋op-log（同交易）─▶ commit ─▶ Applied ─▶ reload（重建-swap）
   空 diff ─▶ Applied（仍 reload、刻意不優化）；Rejected/NoOp/NotFound ─▶ skip reload
```
- **reload＝重建-swap**（Blocker 2）：另建全新 Enforcer 成功才 `*enforcer.write() = new`；失敗保留舊面＋告警＋有界重試；**絕不對 live enforcer 裸呼 load_policy**（clear-then-load 會清空致全域鎖死）。
- **維度辨識**：endpoint 維 current 以 HTTP method 白名單判別（不以「排除其他維度」反推）。
- **menu 維映射**：wire menu id `number[]` → sys_menu 活性轉 route_name（orphan skip）→ v1；讀端反向。

### 3. 刪除／停用／復原（US3/US4）
- **停用斷權**（FR-013）：`roles_of_user` 加 `.filter(Status.eq(1))`（單行、NULL status fail-closed 排除）；下游 RBAC 判定／getUserRoutes／getUserInfo buttons 全生效。self-guard＋R_SUPER 恆禁停用。
- **restorePolicy 三態＋七步鎖序**（Blocker 1、FR-029/030）：見 [research.md R7](./research.md)；核心＝鎖 archive 列→鎖標的活角色列→鎖內重驗同實例（`locked_role.id == archived.role_id`，不等/NULL→notRestorable，**封繼承旁路**）→menu 維驗活性→三態（已 live NoOp／INSERT live／假 id・不可復原 2222）。
- **restorable「角色活性」**＝`deleted_at IS NULL`（＝鎖查詢謂詞＝partial-uniq 索引域）；`status=2` 停用**不阻復原**（停用只作用 roles_of_user、casbin 列本就在 live 表、治理授權不受阻）。
- **roleHome 讀端兜底**（FR-039）：getUserRoutes 下發 home 前驗其在可見樹內；不在→可見樹第一可導航頁；全空→維持預設值（不落 404）。

## 載重不變式

- **快照完整性（archive 缺 protected 無害）**：restore 保真由雙重不變式保證——① 可復原列（reason≠role_soft_delete）必經 revoke，protected-reject 保證 revoke 歸檔列恆 protected=false，restore 反向 INSERT 落 live default false＝逐欄無損；② protected=true 列進不了 archive（FR-018 protected-reject＋seeded 守門①＋grant 恆 false 三路封死，FR-011「含受保護列」歸檔實為防禦性空集合）。**未來翻案風險**（role restore／protected 掛非 seeded／un-protect UI）會使缺欄變靜默降權破口——載入 ADR② won't-add 分析、屆時新刀須自帶 protected 快照欄（NULL=unknown）。
- **繼承旁路封死（Blocker 1）**：restorePolicy 鎖內同實例判定（`locked_role.id == archived.role_id`）＋deleteRole 同交易 archive_all 全維；restore 與 delete 經同一 sys_role 列鎖序列化（EPQ 使等鎖期間被 delete 的角色現形查無）。
- **全域鎖取得順序（防死鎖）**：archive 列 → sys_role 列 → casbin_rule/sys_user_role 列；禁反向；batchDelete 依 role id 升冪。
