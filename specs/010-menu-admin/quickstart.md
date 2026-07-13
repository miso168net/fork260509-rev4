# Quickstart 驗收: 010-menu-admin

**Branch**: `010-menu-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](./plan.md)

端到端驗收指南（非實作碼）。rust 單元／整合＝容器內 `cargo test --workspace`（serial）；前端互動＝CDP 實機（curl≠modal）。前置＝rev4 stack 起（前端 `:42080`、乾淨 DB）＋**憲法 v1.8.0 Amendment 已落地**（島 H＋(d) 錨點——(d) 相依的前端單元「未落地不施工」）。**零 migration**——無 schema 前置。

## 前置

```
# 容器內、serial（host 無 toolchain）
docker compose exec rust-api cargo test --workspace   # 全綠含 7 契約 case＋五負向自證＋併發機器證
grep -n '島 H' .specify/memory/constitution.md         # v1.8.0 已入憲（首個實作單元前）
# 前端 CDP：Edge@9229 WebSocket、quick-login（rev4-cdp 速查）；新 i18n key 後 restart base-web 再 CDP（L-015）
```

## rust 負向自證（守門非恆綠、SC-006 五支）

刻意破壞下列任一，對應測試**須轉紅**（各支防恆綠前置已烤進測試設計）：
1. 拆 protected 守門 → 「protected 選單拒刪」轉紅（★測試標的用**無子項** protected 列〔如 manage_system-settings〕＋斷言拒因＝`protectedMenu`——防被 `hasChildren` 遮蔽恆綠）。
2. 拆環檢測 → 「re-parent 成環拒」轉紅。
3. 拆刪除連動歸檔 → 「同鍵重建零繼承」轉紅（★前置＝**先對測試角色授權該選單、再刪、再同鍵重建**——確保有可繼承列、防空集恆綠）。
4. batch 改逐項提交（非整批） → 「批內一項違規整批零變更」轉紅。
5. 拆 button 維連動（獨有判定或 `menu_button_removed` 歸檔） → 「code 重現零繼承」轉紅（含共用 code 不誤傷的對偶正向測）。

## rust 併發機器證（SC-003、序列化域有效性）

- `deleteMenu(parent)` × `restoreMenu(child)` 併發：以 pg_locks `locktype='advisory'` 觀察後到者等待；終態斷言＝二序列之一、樹無「未刪子掛已刪父」。
- `deleteMenu(M)` × `updateRoleMenu(R, 含 M)` 併發：終態斷言＝不存在「M 已刪而 (R,M,menu) 殘留 live」；同鍵重建後 R 對新列零授權。
- `updateMenu(A, parentId→B)` × `updateMenu(B, parentId→A)` 對向 re-parent 併發：後到者於域內等待→鎖內重驗→`cycleDetected` 拒；終態斷言＝至多一筆成功、樹恆無環（SC-003 第三組）。

## CDP 實機場景

### S1 選單 CRUD 全鏈（US1）
1. 進 `/manage/menu`；樹狀列表載入（fetchGetMenuList 200、非現況必敗；children 巢狀、含停用列）。
2. 新增頁面型選單（合法 routeName）→ 成功；列表可見；**sidebar 不出現（含超管、兩步流）**。
3. 同 routeName 再新增 → `2222 routeNameExists`；非法字元 routeName → `routeNameInvalid`。
4. 編輯：改 menuName/icon/order → 成功；routeName/menuType 欄 edit 模式鎖定（UI）＋繞 UI 直送變更 → `routeNameImmutable`/`menuTypeImmutable`（雙路驗證）。
5. re-parent：掛到停用父層 → 成功；掛到自身子孫 → `cycleDetected`。
6. 刪除 protected 選單（如 manage_system-settings）→ `protectedMenu` 拒。
7. 刪除有未刪子項的目錄 → `hasChildren` 拒（含停用子項案）。
8. 批刪同批含父＋全部子項 → 成功（拓撲序）；批內含 protected → 整批拒、列表零變更。

### S2 兩步流與授權連動（US2）
1. 新增選單 → 到角色管理頁選單授權 modal 勾給測試角色 → 該角色帳號重整後 sidebar 出現。
2. 對已授權選單執行刪除 → 成功；該角色帳號重整後 sidebar 消失；`/manage/policy-archive` 出現 `menu_soft_delete` 歸檔列（**不可復原停用態**、強打後端亦拒）。
3. 同 routeName 重建 → 新選單對任何角色零授權（sidebar 不現、勾選現況空）。
4. 共用 button code 案：兩選單登記同 code、刪其一 → 另一選單頁按鈕能力**存活**（hasAuth 不變）。
5. buttons 編輯移除獨有 code → 歸檔列（`menu_button_removed`）出現、該 code 授權即撤。

### S3 回收桶（US3）
1. 「顯示已刪除」toggle ON → 已刪列（deleted_at 新到舊）＋逐列 restore 鈕；OFF → 回未刪列表。
2. restore 成功 → 回列表（原欄位/parent 保留）；sidebar 不自動出現（零授權）→ 重勾後出現。
3. 同鍵活性衝突 restore → `routeNameExists` 拒；父層已刪 → `parentDeleted` 拒、先復原父層後成功。

### S4 停用分層（US4）
1. 停用已授權選單 → 該角色帳號重整後 sidebar 消失；管理列表仍見（停用態）。
2. 開角色選單授權 modal → **停用選單仍在候選樹、勾選現況保留**（治理域分層）。
3. 停用期間對該角色提交其他選單勾選變更 → 停用選單授權**不被誤撤**（重新啟用後 sidebar 直接恢復、無需重勾）。

### S5 拒因明細（US5）
各拒因於介面呈現專屬訊息（R9 鍵表逐鍵）、三語齊、無 raw key；既有無明細錯誤路徑行為不變。

### S6 role_home 兜底承接（FR-027）
把測試角色 role_home 設為某選單、刪該選單 → 該角色帳號登入**不落 404**、落點為可見樹第一可導航頁（009 兜底、實機案例）。

**residue 紀律**：CDP 建列場景（新增/刪除/重建）用測試專屬 routeName 前綴、跑完精確清理＋**順跑 gate2**（L-138；種子面凍結核對照舊——本刀零 seed 變更、gate2 應全綠）。

## 收刀閘
`cargo test --workspace` 全綠；`pnpm typecheck`＋`tools/fork-delta-lint` 綠；docs-sync `generate`＋三 lint 閘綠；**零 migration＝零 gate 白名單動作**；憲法 v1.8.0＋ADR 0051/0052 accepted；B-060 註記（收刀簿記）。

## agent context
rev4 CLAUDE.md 為手維薄操作手冊（≤250 行 lint 強制），**不走 speckit auto agent-context 機制**——本步 N/A（009 先例；架構影響於收刀走活書 arch-impact＋docs-sync generate）。
