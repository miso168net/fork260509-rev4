# Contract: 010-menu-admin 7 端點

**Branch**: `010-menu-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](../plan.md)

7 端點封閉全集，全數 `Protection::Policy`（require_policy 軌）、**動詞逐條對齊 casbin seed act**（GET×2／POST×3／DELETE×2；政策全 R_SUPER-only、seed 列 id 見 `〔n〕`；getDeletedMenus/restoreMenu 政策列 protected=true＝治理面恢復路徑）。現況 routes.md 零 menu 域端點 → 7 條全 net-new 註冊。envelope `{data,code,msg}` 凍結；成功 `0000`、業務錯誤 `2222`（HTTP 200）、權限不足 `5003`。**零新錯誤碼**。拒因鍵字面＝research R9 表（一因一鍵）。

★契約紀律：每條 method 寫死、router 註冊打錯即該端點全域 5003 → coverage gate 7 條契約 case 兜底（§I.3）。

## 型別（凍結形 vs 新形）

**凍結（不動）**：`Menu = CommonRecord<{parentId:number, menuType:'1'|'2', menuName, routeName, routePath, component?, icon, iconType:'1'|'2', buttons?:MenuButton[]|null, children?:Menu[]|null}> & MenuPropsOfRoute`；`MenuList = PaginatingQueryRecord<Menu>`；`MenuButton = {code, desc}`；`MenuType`／`IconType`。

**新形（ADAPT `rev4-menu-admin.d.ts`、declaration merging `Api.SystemManage`）**：
- `AddMenuReq`＝Menu 可寫欄集（menuType/menuName/routeName/routePath/component/icon/iconType/parentId/status/order/buttons/query＋route meta 欄；無 id/審計欄）
- `UpdateMenuReq = {id} & AddMenuReq 同欄`（★routeName/menuType **收但不可變**——後端比對現值、不同→`routeNameImmutable`/`menuTypeImmutable` 拒；FR-005 拒絕路徑的 wire 載體、鏡像 009 roleCode 手法）
- `BatchDeleteMenuReq = {ids: number[]}`；`RestoreMenuReq = {id: number}`；`GetDeletedMenusParams = {current, size}`
- （明細 data 形隨 impl 定：批刪 blocked 清單等、ADR 0050 範式）

## 端點表

| # | path | method | 〔seed；protected〕 | req | res data |
|---|---|---|---|---|---|
| 1 | `/systemManage/getMenuList/v2` | GET | R_SUPER〔25；false〕 | `{current?, size?}`（無參→預設常數） | `MenuList`（records=頂層＋children 巢狀、含停用不含已刪、頂層分頁；R4） |
| 2 | `/systemManage/addMenu` | POST | R_SUPER〔28；false〕 | `AddMenuReq` | `null`（0000；零 casbin 寫＝兩步流）｜`2222 routeNameInvalid`／`routeNameExists`／`parentNotFound`／`parentDeleted` |
| 3 | `/systemManage/updateMenu` | POST | R_SUPER〔29；false〕 | `UpdateMenuReq` | `null`（無變更→提前 no-op）｜`2222 routeNameImmutable`／`menuTypeImmutable`／`parentNotFound`／`parentDeleted`／`cycleDetected`／`notFound`；buttons 移除致絕版→連動歸檔（reason=`menu_button_removed`）→Applied 才 reload |
| 4 | `/systemManage/deleteMenu` | **DELETE** | R_SUPER〔30；false〕 | `{id}` | `null`（軟刪＋同交易連動歸檔 menu 維跨全角色＋獨有 button 維、reason=`menu_soft_delete`→Applied 才 reload）｜`2222 protectedMenu`／`hasChildren`／`notFound` |
| 5 | `/systemManage/batchDeleteMenu` | **DELETE** | R_SUPER〔31；false〕 | `BatchDeleteMenuReq`（去重；拓撲序 child-first；no-partial 自管 txn） | `null`｜`2222`（個別守門鍵＋data 明細、整批零變更） |
| 6 | `/systemManage/getDeletedMenus` | GET | R_SUPER〔64；**true**〕 | `GetDeletedMenusParams` | `PageRes<Menu>`（已刪列平面、children=null、deleted_at DESC；R5） |
| 7 | `/systemManage/restoreMenu` | POST | R_SUPER〔65；**true**〕 | `RestoreMenuReq{id}` | `null`（域內鎖列＋重驗→成對清空 deleted_at/by、原 status 保留、★不回灌授權）｜`2222 routeNameExists`（含 23505 兜底收斂）／`parentDeleted`／`notFound` |

全部寫端＝序列化域成員（R1：advisory→FOR UPDATE→鎖內重驗→寫→op-log→commit）；觸及授權變更者（#3 絕版路徑、#4、#5）成功才 reload（重建-swap、009 基建）。**生效語意（FR-016 明文）**：API 判定即時（每請求 DB-fresh enforce）、前端選單／按鈕顯隱等下次 getUserRoutes／載入更新；本刀 MUST NOT 做即時推播。

## 009 寫端連動改動（本刀契約外、行為語意不變）

- `set_role_dimension`（updateRoleMenu／updateRoleButton）＋`restorePolicy`：入序列化域（各加 advisory 首動作＋鎖內重驗沿既有）——對 wire 契約零影響。
- 治理域換源四處（getMenuTree／getRoleMenu 反查／menu_ids_to_route_names／getAllButtons）：候選/回讀集合語意變更＝「未刪」（含停用）——**getMenuTree／getAllButtons 回應內容在有停用選單時變寬**（user 已核可、spec US4）。
- `restorePolicy` reason gate 集合擴充（R6）：對既有列行為不變（新 reason 僅 010 起產生）；拒因復用 009 既有 `biz.policy.notRestorable` 鍵（零新增、R9）。

## 前端 fetcher 對帳（R10）

6 支新 fetcher（WRAPPER `rev4-menu-admin.ts`：add／update／delete／batchDelete／getDeleted／restore）＋1 支復用凍結 `system-manage.ts`（`fetchGetMenuList`〔:34〕、沿 barrel、絕不重建）＝**6＋1＝7 對帳吻合**。新 fetcher 動詞逐條對齊上表（FR-002）。
