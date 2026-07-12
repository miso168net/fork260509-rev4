# Contract: 009-role-admin 20 端點

**Branch**: `009-role-admin` | **Date**: 2026-07-12 | **Plan**: [plan.md](../plan.md)

20 端點封閉全集，全數 `Protection::Policy`（require_policy 軌）、**動詞逐條對齊 casbin seed act**（GET×11／POST×7／DELETE×2、對應 seed 政策 23 列）。現況 routes.md 零 role 域端點 → 20 條全 net-new。envelope `{data,code,msg}` 凍結；成功 `0000`、業務錯誤 `2222`（HTTP 200）、權限不足 `5003`。**零新錯誤碼**。

★契約紀律：每條 method 寫死、router 註冊動詞打錯即該端點全域 5003 → §7 coverage gate 20 條契約 case 兜底。`〔n〕`＝seed 政策列 id。

## 型別（凍結形 vs 新形）

**凍結（不動）**：`Role = CommonRecord<{roleName, roleCode, roleDesc}>`；`CommonRecord = {id, createBy, createTime, updateBy, updateTime, status:'1'|'2'|null}`；`AllRole = Pick<Role,'id'|'roleName'|'roleCode'>`；`RoleList = PageRes<Role>`；`MenuTree`；`MenuButton = {code, desc}`。

**新形（ADAPT `rev4-role-admin.d.ts`、declaration merging `Api.SystemManage`）**：
- `Endpoint = { path: string; method: string }`（getAllEndpoints 回應項＝updateRoleEndpoints desired 項、同形共用）
- `ArchivedPolicy = { id; ptype; v0..v5; archiveReason; archivedAt; archivedBy; roleId; restorable: boolean; dimension: 'menu'|'button'|'endpoint' }`（restorable/dimension 後端下發）
- `ArchivedPolicySearchParams = RecordNullable<{ roleCode?; dimension?; current; size }>`；`ArchivedPolicyList = PageRes<ArchivedPolicy>`
- 寫端請求形：`AddRoleReq`／`UpdateRoleReq`（Pick 凍結 Role）／`UpdateRoleMenuReq{roleId, menuIds:number[]}`／`UpdateRoleButtonReq{roleId, buttons:string[]}`／`UpdateRoleEndpointsReq{roleId, endpoints:Endpoint[]}`／`UpdateRoleHomeReq{roleId, home}`／`RestorePolicyReq{id}`
- （可選）B-047 明細 data 形：`{userCount:number}`／`{blocked:{target,dimension}[]}`

## P1 role CRUD（6）

| # | path | method | 政策角色〔seed〕 | req | res data |
|---|---|---|---|---|---|
| 1 | `/systemManage/getRoleList` | GET | R_SUPER＋R_ADMIN〔12,13〕 | `RoleSearchParams`（roleName 模糊／roleCode 模糊／status 等值＋current/size） | `PageRes<Role>` |
| 2 | `/systemManage/getAllRoles` | GET | 三角色〔14,15,16〕 | — | `AllRole[]`（僅活性＋啟用；FR-002） |
| 3 | `/systemManage/addRole` | POST | R_SUPER〔21〕 | `{roleName, roleCode, roleDesc, status}` | `null`（成功 0000）｜`2222 biz.role.codeExists`／`codeInvalid` |
| 4 | `/systemManage/updateRole` | POST | R_SUPER〔22〕 | `{id, roleName?, roleDesc?, status?}`（roleCode 變更→`codeImmutable`；全 None→no-op 不 bump 時戳/不落稽核 B-050） | `null`｜`2222 codeImmutable`／`cannotDisableSelfRole`／`biz.role.superCannotDisable` |
| 5 | `/systemManage/deleteRole` | **DELETE** | R_SUPER〔23〕 | `{id}` | `null`｜`2222 seededProtected`／`inUse`〔data{userCount}〕／`cannotDeleteSelfRole` |
| 6 | `/systemManage/batchDeleteRole` | **DELETE** | R_SUPER〔24〕 | `{ids:number[]}`（逐項驗證整批拒 no-partial、自管 txn） | `null`｜`2222`（同守門、整批零變更） |

## P2 三維授權讀寫（6、政策 protected=true）

| # | path | method | 〔seed〕 | req | res data |
|---|---|---|---|---|---|
| 7 | `/systemManage/getRoleMenu` | GET | R_SUPER〔32〕 | `{roleId}` | `number[]`（menu id、route_name 反查、FR-023 讀端反向） |
| 8 | `/systemManage/updateRoleMenu` | POST | R_SUPER〔33〕 | `UpdateRoleMenuReq` | `null`（Applied→reload）｜`2222 protectedRevoke`〔data{blocked[]}〕 |
| 9 | `/systemManage/getRoleButton` | GET | R_SUPER〔53〕 | `{roleId}` | `string[]`（button code） |
| 10 | `/systemManage/updateRoleButton` | POST | R_SUPER〔54〕 | `UpdateRoleButtonReq` | `null`｜`2222 protectedRevoke` |
| 11 | `/systemManage/getRoleEndpoints` | GET | R_SUPER〔56〕 | `{roleId}` | `Endpoint[]` |
| 12 | `/systemManage/updateRoleEndpoints` | POST | R_SUPER〔57〕 | `UpdateRoleEndpointsReq` | `null`｜`2222 protectedRevoke` |

全量替換語意（FR-017）：desired 全集 → diff → protected-reject（任何寫之前）→ archive-move＋grant → op-log → reload（重建-swap）。三維寫端 caller 先鎖 sys_role（R7），facade 收 caller txn、不 pre-read。

## 支撐讀（4）

| # | path | method | 〔seed；protected〕 | res data | 用途 |
|---|---|---|---|---|---|
| 13 | `/systemManage/getMenuTree` | GET | R_SUPER〔27；false〕 | `MenuTree[]` | menu-auth-modal 樹候選 |
| 14 | `/systemManage/getAllPages` | GET | R_SUPER〔26；false〕 | `string[]` | roleHome 候選＝頁面全集 |
| 15 | `/systemManage/getAllButtons` | GET | R_SUPER〔52；**true**〕 | `string[]`（sys_menu.buttons 聯集去重） | button-auth-modal 候選 |
| 16 | `/systemManage/getAllEndpoints` | GET | R_SUPER〔55；**true**〕 | `Endpoint[]`（ROUTES const 濾 Policy 級、含 path＋method） | endpoint-auth-modal 候選（registry 真源、FR-025） |

## P2 roleHome（2）

| # | path | method | 〔seed〕 | req | res data |
|---|---|---|---|---|---|
| 17 | `/systemManage/getRoleHome` | GET | R_SUPER〔34〕 | `{roleId}` | `string`（role_home） |
| 18 | `/systemManage/updateRoleHome` | POST | R_SUPER〔35〕 | `UpdateRoleHomeReq` | `null`（op-log 同交易）；寫端不驗一致性（讀端兜底 FR-039） |

## P3 回收桶（2、政策 protected=true）

| # | path | method | 〔seed〕 | req | res data |
|---|---|---|---|---|---|
| 19 | `/systemManage/getArchivedPolicies` | GET | R_SUPER〔70〕 | `ArchivedPolicySearchParams`（roleCode／dimension 雙濾＋分頁） | `PageRes<ArchivedPolicy>`（archived_at desc、restorable 隨列下發） |
| 20 | `/systemManage/restorePolicy` | POST | R_SUPER〔71〕 | `RestorePolicyReq{id}` | `null`（Applied→reload）｜`0000`（已 live NoOp、歸檔列仍消費）｜`2222 notRestorable`（假 id／role_soft_delete／同實例不符／NULL role_id／menu orphan） |

restorePolicy 七步鎖序見 [research.md R7](../research.md)。

## 前端 fetcher 對帳（R9）

16 支新 fetcher（WRAPPER `rev4-role-admin.ts`）＋4 支复用凍結 `system-manage.ts`（fetchGetRoleList／fetchGetAllRoles／fetchGetMenuTree／fetchGetAllPages、沿 barrel、絕不重建）＝**16＋4＝20 對帳吻合**。新 fetcher 動詞逐條對齊上表（FR-003）。
