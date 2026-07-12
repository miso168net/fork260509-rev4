# Data Model: 010-menu-admin

**Branch**: `010-menu-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](./plan.md)

schema 全於 002 凍結基線（出處＝`docs/generated/reference/schema.md` 實庫快照）。**本刀零 migration、零新表、零加欄、零 seed 變更**（比 009 更輕）；唯一資料語意擴充＝`archive_reason` 取值集合加兩值（欄型不變）。

## 實體（皆凍結基線、零結構變更）

### sys_menu（選單，archetype A 業務全 6 欄）
六審計欄＋`menu_type smallint`（1=目錄／2=頁面）＋`menu_name`／`route_name`／`route_path`／`component`／`icon`／`icon_type smallint`＋`parent_id bigint NULL`（NULL=頂層、wire 映 `parentId=0`）＋`status smallint`（1=啟用／2=停用）＋`order`＋`buttons jsonb`（`[{code,desc}]`）＋`query jsonb`＋route meta 欄（`i18n_key`／`keep_alive`／`constant`／`href`／`hide_in_menu`／`active_menu`／`multi_tab`／`fixed_index_in_tab`）＋`protected bool`＋`menu_memo`。partial-uniq `sys_menu_route_name_active_uniq (route_name) WHERE deleted_at IS NULL`。
- **治理域**＝`deleted_at IS NULL`（含停用；facade 新讀 `list_governed`）；**顯示域**＝`status=1 AND deleted_at IS NULL`（既有 `list_active`）。
- **不可變欄**（H4）：`route_name`／`menu_type` 建後不可變（後端顯式拒；DB 無約束、閘在寫端）。
- **route_name 形制**：`^[A-Za-z0-9_-]{1,100}$`（addMenu 單點把關；R9）。
- **protected 8 列**（seed）：home＋manage 樹（manage／manage_user／manage_role／manage_menu／manage_user-detail／manage_system-settings／manage_policy-archive）——deleteMenu 守門①標的。
- seed 78 列全 status=1、未刪；demo 67 列本刀不動（D2）。

### casbin_rule（現役授權、唯讀消費＋連動歸檔標的）
menu 維列＝`(p, role_code, route_name, 'menu')`；button 維列＝`(p, role_code, button_code, 'button')`。deleteMenu／buttons 絕版之連動歸檔標的；**本刀零 grant 類寫入**（兩步流 FR-004/030——授權授予唯一路徑仍是 009 全量替換寫端）。

### sys_casbin_policy_archive（授權歸檔、14 欄含 role_id）
本刀寫入路徑＝deleteMenu 連動（menu 維＋絕版 button 維）與 updateMenu buttons 絕版連動。`archive_reason` 取值集合擴充（**欄型 varchar(32) 不變**）：

| reason | 來源 | 可手動復原 |
|---|---|---|
| 撤銷類（menu_revoke 等、009 既有） | 全量替換 diff 撤銷 | 是（同實例 gate） |
| `role_soft_delete`（009 既有） | 角色刪除連動 | **否** |
| ★`menu_soft_delete`（010 新增） | 選單刪除連動（menu 維跨全角色＋獨有 button 維） | **否** |
| ★`menu_button_removed`（010 新增） | buttons 編輯絕版連動 | **否** |

不可手動復原集合 gate **enforce 於 restorePolicy 權威判定**（與 list restorable 旗標共用單一判定 fn、R6）。role_id＝各歸檔列 v0 查 sys_role 現值 id（查無→NULL 誠實退化）。

### sys_role／sys_user_role（唯讀消費）
role_id 回填查找；本刀不動角色域寫端（序列化域僅把 009 的 menu/button 維寫端拉入域、行為語意不變）。

### 端點登記表（非 DB 實體）
ROUTES const ＋7 條新註冊（動詞對齊 seed act、R3）；契約 coverage gate 7 條。

## 選單域狀態機

### 1. 選單生命週期（US1／US3）
```
（無）─addMenu（形制＋同鍵衝突＋parent 驗；零 casbin 寫）─▶ 啟用(status=1)
   啟用 ◀─updateMenu status─▶ 停用(status=2)（顯示域即隱、治理域不動＝授權保留）
   啟用/停用 ─deleteMenu（守門①protected ②未刪子項）─▶ 軟刪(deleted_at/by 成對)
        ＋同交易連動歸檔（menu 維跨全角色 reason=menu_soft_delete＋獨有 button 維）─▶ Applied 才 reload
   軟刪 ─restoreMenu（域內鎖列＋同鍵活性衝突驗＋parent 驗）─▶ 啟用/停用（原 status 保留）
        ★不回灌授權（零授權、重勾）；23505 兜底收斂 routeNameExists
   同 route_name 重建（partial-uniq 允許）─▶ 新列零繼承（H2：現役無殘留＋歸檔 reason gate 雙封）
```
- **不可變欄**：update 收 routeName/menuType 但比對現值、不同→顯式拒（鏡像 009 roleCode 手法）。
- **re-parent**：域內環檢測（上溯 ≤64、遇 self→拒）＋parent 驗（未刪即可、停用不擋、parentId=0 豁免）。
- **無欄位變更提交**：提前 no-op（不 bump 時戳、不落稽核；鏡像 009 B-050）。

### 2. 批次刪除（US1、no-partial＋拓撲序）
```
ids 去重 ─▶ 域內讀批內全列（不存在/已刪→整批拒）─▶ 樹深 DESC 排序（child-first）
  ─▶ 逐列：守門①②（批內已刪子項於同 txn 現形→父自然過門；批外未刪子項→整批拒）
  ─▶ 逐列軟刪＋連動歸檔 ─▶ op-log ─▶ commit（任一步拒→rollback 整批零變更）─▶ Applied 才 reload
```

### 3. 序列化域（H1、全寫端骨架）
```
begin ─▶ pg_advisory_xact_lock(0x7265_7634_6D65_6E75)（txn 首動作）
  ─▶ 標的列 FOR UPDATE ─▶ 鎖內重驗全部守門前提 ─▶ 寫＋連動歸檔 ─▶ op-log ─▶ commit（自動釋放）
域成員：樹五寫端＋set_role_dimension（menu/button 維）＋restorePolicy；set_role_endpoints 不屬域。
```

## 載重不變式

- **同鍵重建零繼承（H2；009 spec SC-004 之選單版對偶＝本 spec SC-002）**：雙封——①現役零殘留（序列化域使 deleteMenu×updateRoleMenu 互斥、phantom grant 不可達；連動歸檔掃盡 menu 維＋獨有 button 維）；②歸檔不可回灌（`menu_soft_delete`／`menu_button_removed` reason gate 落於 restore 權威判定）。button 維同理：絕版 code 零 live 殘留＋歸檔不可復原→code 重現零繼承。
- **樹結構不變式（H3）**：域內單線程使「活子掛軟刪父」「對向 re-parent 成環」「新增子項×刪父交錯」全部結構性不可達；謂詞釘死＝「未刪子項（不論啟停）」擋刪。
- **兩域分層（H4）**：治理域（未刪）保證停用≠撤銷；顯示域（啟用∧未刪）保證停用即隱。getAllPages（顯示域）候選收縮＝已知限制（FR-032、復原即回）。
- **role_home 懸空**：009 FR-039 讀端兜底承接（本刀零寫端 cascade）；「首頁指向被刪選單」驗收案例錨定。
- **鎖取得順序**：advisory（域首動作）→ archive 列 → sys_role 列 → sys_menu 列 → casbin_rule 列；域內單線程使內部序自由、域外（endpoint 維）與域內僅共用 sys_role 單列鎖、無死鎖環。
