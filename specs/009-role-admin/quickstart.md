# Quickstart 驗收: 009-role-admin

**Branch**: `009-role-admin` | **Date**: 2026-07-12 | **Plan**: [plan.md](./plan.md)

端到端驗收指南（非實作碼）。rust 單元／整合＝容器內 `cargo test --workspace`（serial）；前端互動＝CDP 實機（curl≠modal、rev3 定論）。前置＝rev4 stack 起（前端 `:42080`、乾淨 DB）＋m007 已 migrate。

## 前置

```
# 容器內、serial（host 無 toolchain）
docker compose exec rust-api cargo test --workspace   # 全綠含 20 契約 case＋五負向自證＋reload 不鎖死
docker compose exec rust-api sh -c 'ls migration/src/m007*'  # m007 存在
# 前端 CDP：Edge@9229 WebSocket、quick-login（rev4-cdp-driving 速查）；新 i18n key 後 restart base-web 再 CDP（L-015）
```

## rust 負向自證（守門非恆綠、比照 007/008）

刻意破壞下列任一，對應測試**須轉紅**（SC-007／SC-013）：
1. 拆 protected-reject → 「含 protected 撤銷整批拒零變更」轉紅（＋斷言「整批拒後 archive 零新列」，R2 錨定不變式）。
2. 拆 self-guard（deleteRole／disableRole 兩路）→ 自鎖測試轉紅。
3. restore 判定去掉 `id == role_id` 同實例比對 → 「同 code 重建後舊列不可復原」轉紅。
4. batch 改逐項提交（非整批） → 「批內一項違規整批零變更」轉紅。
5. **restore 拔出 FOR UPDATE 鎖序**（Blocker 1）→ restore-during-delete 併發測試轉紅（殘留 live 授權被同 code 重建繼承）。
6. **reload 改對 live enforcer 裸呼 load_policy**（Blocker 2）→ 「reload 失敗不鎖死」測試轉紅（注入壞 DB conn 使重建失敗、斷言舊面續 allow R_SUPER＋告警留痕）。

## CDP 實機場景

### S1 role CRUD 全鏈（US1）
1. 進 `/manage/role`；列表載入（fetchGetRoleList 200、非現況必敗）。
2. 新增角色（合法 code）→ 成功；再以同 code 新增 → `2222 codeExists` 具體訊息。
3. 編輯 roleName/roleDesc → 成功；試改 roleCode：UI 有輸入欄→提交必拒 `codeImmutable`；UI 無該欄→以契約 case 為準、於驗收 report 註記（明確二擇、不得靜默跳過）。
4. 刪除掛有使用者的角色 → 拒、訊息**含實際人數**（B-047 明細）。
5. 批刪含一違規項 → 整批拒、列表零變更。
6. 刪自己所屬角色 → `cannotDeleteSelfRole`（自傷面：用測試角色/帳號、非操作者自身）。
7. 刪除任一種子角色（R_SUPER/R_ADMIN/R_USER_COMMON）→ 拒、`seededProtected` 訊息（SC-001 守門矩陣種子路的實機半邊）。

### S2 三維授權面板（US2）
1. 開 menu-auth-modal → 樹候選（getMenuTree）＋現況勾選（getRoleMenu）；改勾選提交 → 成功；重開回讀一致。
2. 開 button-auth-modal → 候選＝buttons 聯集；勾選提交回讀一致。
3. 開 **endpoint-auth-modal（net-new）** → 候選＝getAllEndpoints（path 群組樹、NTree check-strategy=child＋synthKey）；群組級勾選提交回讀一致。
4. 構造含受保護項的撤銷提交 → 整批拒、明細列出被擋目標（protectedRevoke data{blocked[]}）。
5. **換角色登入驗收縮/擴張**（demo menu 當素材）：撤某角色端點授權 → 該角色成員下一請求該端點 → `5003`（API 即時）；選單/按鈕顯隱於重新載入後收縮（前端生效延遲、明文）。

### S3 roleHome＋讀端兜底（US6／FR-039）
1. 改角色首頁（getAllPages 候選）提交 → 該角色帳號重登落新首頁。
2. **兜底驗收**：把角色首頁設成該角色看不見的頁（或撤掉該首頁的選單授權）→ 該角色帳號登入**不落 404**、落點為可見樹第一可導航頁。
3. 全角色停用/空授權帳號登入 → 維持預設落點、選單空白（不崩）。

### S4 回收桶三態（US4）
1. 進 `/manage/policy-archive`（新頁、三語譯文齊、無 raw key）；列表 archived_at desc、來源角色×維度雙濾。
2. 復原可復原列 → 授權回現役、列消失；受影響角色成員下請求恢復。
3. 復原「已在現役」列 → 成功無作用、列仍消費移除。
4. 不可復原列（role_soft_delete／同 code 重建異實例／NULL role_id）→ 停用態＋強打後端 `notRestorable`。

### S5 停用斷權即時性（US3／D6）
1. 停用某測試角色（僅掛測試帳號）→ 該帳號下一受管制請求 `5003`（API 即時）；重載後選單收縮。
2. 停用自己所屬角色 → `cannotDisableSelfRole`；停用 R_SUPER → `superCannotDisable`。
3. 重新啟用 → 授權恢復。

### S6 B-047 明細插值
各拒因（inUse{userCount}／protectedRevoke{blocked}）於介面呈現具體插值、三語齊、無 raw key；既有無明細錯誤路徑行為不變。

## 收刀閘
`cargo test --workspace` 全綠；`pnpm typecheck`＋`tools/fork-delta-lint` 綠；docs-sync `refresh`＋`generate`＋三 lint 閘綠；m007 走 gate1 結構白名單＋同 commit（L-109）；活書 §6 as-built 更新走收刀 arch-impact（不入 tasks）。

## agent context
rev4 CLAUDE.md 為手維薄操作手冊（≤250 行 lint 強制），**不走 speckit auto agent-context 機制**——本步 N/A（架構影響於收刀走活書 arch-impact＋docs-sync generate）。
