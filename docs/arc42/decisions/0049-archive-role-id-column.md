---
id: "0049"
title: 授權歸檔表加「來源角色識別」欄（m007 role_id）——restorability 去牆鐘化＋protected 欄 won't-add 分析
date: 2026-07-12
status: draft
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-12 009-role-admin brainstorm D5（user 拍板 2026-07-11~12）＋plan research R2；消化 B-034（rev3 015/020 遺留）"
tags: [schema, authz, governance, migration]
---

## 背景

rev3 的回收桶 restorability 判定靠 `created_at`/`archived_at` 牆鐘比對——B-034 記錄此缺口：牆鐘法依賴「刪除→重建間時鐘單調」的假設，時鐘回撥或非單調即失真。rev4 的 `sys_casbin_policy_archive`（002 凍結基線）無來源角色欄：同 code 角色刪除重建後，歸檔列無從區分「這列屬舊實例還是新實例」——restorable 判定只能落在 code 粒度、「經 restore 把舊實例授權灌進同 code 新角色」的繼承旁路無從封死。

## 決定

**m007**（本刀唯一結構變更、gate1 STRUCTURAL_ADDITIVE_ALLOWLIST 同 commit〔L-109〕）：

```
up:   ALTER TABLE sys_casbin_policy_archive ADD COLUMN role_id bigint NULL;
down: ALTER TABLE sys_casbin_policy_archive DROP COLUMN role_id;
```

- 型別 `bigint`（對齊 `sys_role.id`）；**nullable**；**不設參照約束**（歸檔列壽命長於角色列、不與角色列生命週期耦合——避免對治理表引入無收益的寫入約束）；**無 DEFAULT**（NULL＝「歷史列未知」的誠實語意、設預設值反而汙染判定）；**不加索引**（治理表量級小、主查詢由既有 `idx_casbin_archive_role_dim (v0,v2)` 覆蓋）。
- 本刀後所有歸檔寫入路徑（revoke 與 role_soft_delete 兩路）MUST 填 `role_id`；m007 前歷史列自然 NULL → restorable 判 **不可復原**（誠實退化、不猜測）。
- restorability 判定（去牆鐘化）＝ `archive_reason ≠ 'role_soft_delete'` **且** 現存同 code 活角色 `id == archived.role_id`（同實例）——同時封死「經 restore 把舊實例授權灌進同 code 新角色」的繼承旁路（島 G5、鎖內重驗）。

**★archive 缺 `protected` 欄 won't-add 分析**（research R2、記錄在案）：

archive 表對照 live `casbin_rule` 11 欄，唯一缺欄＝`protected`。**對本刀 restore 完整性影響＝零**，不加欄——依據三不變式：
① 可復原列必經 revoke 路徑，而 protected-reject（G2）保證含 protected 列的撤銷整批拒→**revoke 歸檔列原值恆 `protected=false`**，restore 反向 INSERT 落 live default false＝逐欄無損還原；
② protected=true 列結構上進不了 archive：基線 19 列 protected 全 v0=R_SUPER（seeded、刪除守門①擋死其連動歸檔路）＋grant 恆寫 false＋un-protect 經 UI 不做——三路封死；
③ FR-040 明文本刀唯一結構變更＝role_id 欄，加 protected 欄需 spec amendment 且對現行 restore 零收益（舊列只能 NULL 或猜測）。

**★未來翻案觸發條款**：任何後續刀若引入 role restore、把 protected 政策掛上非 seeded 角色、或將 un-protect UI 化——上列不變式即破，缺欄變成靜默降權破口（restore 後 protected true→false、原受保護列變可撤銷）；**屆時該刀 MUST 自帶 protected 快照欄**（NULL=unknown 誠實退化）並復核本 ADR。

## 後果

- B-034 消化（收刀時 BACKLOG 刪列）；restorable 同實例判定與列上 roleId 下發隨本刀交付（★回收桶「依來源角色過濾」走既有 v0/roleCode 欄與 `idx_casbin_archive_role_dim`、不依賴本欄）。
- restore INSERT 顯式寫 `protected=false`（自我文件化①不變式、不默默吃 DB default）。
- protected-reject 負向測試旁補「整批拒後 archive 零新列」斷言（②不變式的測試錨定）。
- 歷史歸檔列（NULL role_id）永久不可手動復原——已明文接受的退化代價。
