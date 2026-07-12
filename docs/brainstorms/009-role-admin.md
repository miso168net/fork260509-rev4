# 009-role-admin 刀 brainstorm — 角色管理頁＋casbin 授權治理寫端（admin 管理面家族第一刀；消化 B-034／B-047／B-049／B-050 全部＋B-061 三分之一）

**admin 管理面家族**（role → user → menu → audit → ip-rule 頁）**第一刀**。auth family 五刀收官後的新方向（user 拍板 2026-07-11）。核心＝把 002 就預埋好的「規劃 API 面」接成活的：role 域 **20 端點（現況＝零）**＋**casbin 授權治理寫端**（全量替換＋protected-reject＋revoke 必歸檔）＋**回收桶頁**。選 role 頁開局的理由：casbin 治理寫端是整個管理面的權力核心——user／menu 頁的授權語意都踩在它上面；先立治理狀態機，家族後續刀只消費、不重設計。

上游輸入：**ADR 0023**（casbin 政策 seed 入基線——本刀 20 端點的 Policy 政策**全數已 seed、零 seed migration**）、ADR 0015（casbin 委派建表＋治理欄）、ADR 0027（`require_policy` 骨架——DB-fresh roles→enforce→拒 `5003`）、ADR 0032（gate2 seed additive 白名單——本刀唯一 migration m007 走此軌）、ADR 0039（gate1 結構 additive 白名單）、ADR 0041（「零新 key」釋義）、ADR 0002（datetime 慣例）、ADR 0004（13 碼矩陣）、ADR 0006（軟刪慣例＝partial-uniq＋讀端濾）；憲法 §I.1（base-web 權威——模板 role 頁的功能面即設計範圍下限）、§I.2（menu casbin enforce；demo menu 全集入 seed、可見性由勾選層治理——**本刀的 updateRoleMenu 正是那個勾選層**）、§I.3（envelope `{data,code,msg}` 凍結、business error `2222`＋HTTP 200、`PageRes` 形、`msg`＝i18n key）、§I.5（rust-api 全新寫＋防回歸條款）、§I.6（六審計欄）、§I.7（行為島進場規則）、§III（fork-delta 紀律；MODAL-WIRING (a)(b)(c)(e) 已授權、ADAPT／WRAPPER 預設軌道）；L-015（vite stale locale——新 i18n key 後 restart 再 CDP）、L-119（`.vue` template 標記用 `<!-- -->`）、L-109（gate 白名單同 commit）、L-121~L-123／L-131／L-135（CDP 驅動坑）。

---

## rev3 受控參照（唯讀、憲法 §I.5 全新寫、code 不拷貝）

rev3 role 頁演進鏈＝ **011（menu-auth）→ 015（治理島 archive/restore/gate）→ 016（button＋endpoint 兩維度）→ 020（角色刪除連動 archive）**；DESIGN §4.2 為 casbin 治理狀態機凍結權威。偵察主要依據非 rebase 版 rev3（`fork260509-rev3/docs/`、2026-07-02、含全部四刀＋整併 REVIEW），由唯讀 agent 彙整、關鍵結論已對照 rev4 現況覆核。

**沿用（已驗證、照結論施工）**：
- 寫入語意＝**全量替換**（desired 全集→後端 diff→revoke＋grant），非增量（016 §2.1 hard-replace）。
- **DB-first**：直寫 `casbin_rule`、絕不走 enforcer MgmtApi 寫面（011 §7 ★B1 校正——原 brainstorm 誤走 MgmtApi 被 `/speckit-analyze` 抓出）；與 op-log **同交易原子**（015 收束、非 011 波 2 的 best-effort）。
- **reload-on-Applied**（含空 diff、刻意不優化，源 rev2-035 FR-006；015 §4.2 ③）；Rejected／NoOp／NotFound → skip。
- **protected-reject**：to_revoke 含 `protected=true` 列→整批 Rejected、零變更、`2222`（§4.2 invariant ②）；un-protect／re-protect 經 UI 不做（015 §3.2 拍板 A、防 lock-out by-design）。
- **刪除三層守門（序固定）**：①seeded（hardcode 三角色）②in-use（`sys_user_role` 有指派不可刪、防孤兒指派）③self-role（操作者所屬、自鎖防護）（011 §3-D3＋020）；**批次逐項驗證、整批拒 no-partial**（011 §3-D8）；**role 軟刪單向、不做 role restore**（020 §5）。
- **刪除連動歸檔**（020、P-011-1 HIGH 根因）：軟刪同交易把該 role code **全部** casbin p-policy（三維、含 protected——角色將消失、protected-reject 不適用）archive-move 進 `sys_casbin_policy_archive`、reason=`role_soft_delete`；否則 partial-uniq 允許 code 重用→同 code 新角色**靜默繼承**舊授權（含 API 存取權）。
- **restore 三態**（015 §4）：archive→live 反向 move＋archive 列刪；已 live→NoOp `0000`（archive 列仍消費）；假 id→`2222`。`role_soft_delete` 列不可手動復原（020 §4.1）——`restorable: bool` 後端單一真相下發、前端不硬編 reason；拒絕回 `2222 biz.policy.notRestorable`（縱深防禦、非只靠前端隱藏）。
- **回收桶維度辨識**（016 §3.4 拍板 3）：不改 `archive_reason`；dimension 由 v2 推導（`menu`／`button`→原值、其餘→`endpoint`）。
- **endpoint 維**（016）：授權粒度＝**(path, method) 雙鍵**；current 辨識用 **HTTP method 白名單**（刻意不用 `NOT IN ('menu','button')` 以免脆弱）；★絕無 `v2='endpoint'` 平行編碼——enforce 列即 `(v0=role, v1=path, v2=method)`。**鎖出安全零 migration 解**：19 列 protected seed 已涵蓋恢復路徑（getRole/updateRoleEndpoints、getArchivedPolicies/restorePolicy、getSystemSettings…）→ 超管永遠改不掉自己的恢復路徑。
- **grant-during-delete 鎖序**（020、user 拍板 A）：casbin 寫端同交易 `FOR UPDATE` 鎖該 `sys_role` 列，防刪除與 grant 競態。
- **menu 維 id↔route_name 映射**（011 §2.4 crux）：modal 用 menu id（NTree key-field=id）、casbin v1 用 route_name，經 `sys_menu` 活性表轉換、orphan skip。
- **roleHome**（011 §3-D6）：entity 讀寫 `sys_role.role_home`（非 casbin policy）、op-log 原子；wire `getRoleHome→string`／`updateRoleHome {roleId, home}`；home 選項來自 `getAllPages`。
- 前端坑：endpoint modal 需 path 群組（`NTree check-strategy=child`＋synthKey 加固）；i18n Schema 先行＋locale 同 commit；CDP 不可 defer（curl≠modal、016 §6）。

**升級（rev3 明確留下的缺口、本刀補齊）**：
- **B-034**：archive 表存來源 `role_id`——restorability 判定去牆鐘化（rev3 靠 created_at/archived_at 比對、假設刪除→重建間時鐘單調）＋回收桶「依來源角色過濾」UX（rev3 v1 defer）。
- **B-047**：protected-reject 等拒因訊息具體化（rev3 只回泛化訊息、facade 帶明細但 wire 不載）——本刀拍②結構化明細案（見 §5）。
- **B-049**：批次軟刪自管 transaction（rev3 010 用 sentinel DbErr 借錯誤型當交易控制流）——batchDeleteRole 起手即自管 txn。
- **B-050**：部分更新全 None 提前 no-op 入 handler/facade 慣例（rev3 025 遺留：空 body 仍 bump 時戳＋寫 no-op 審計列）。
- **getAllEndpoints 真源**：ROUTES const 過濾 Policy 級（rev3 用「各角色 policy 聯集」湊、明載 caveat 留 open；rev4 的 router 單檔真源直接解——registry 與 enforce 面同源）。
- **grant 治理欄**：新 policy 列 `protected=false`＋`created_at/created_by` 補寫（rev3 011 波 2 經 adapter 只寫 8 基底欄、治理欄留空；rev4 DB-first 自寫、直接補齊）。

**不採／延後**：
- **M-6 三維 grant no-escalation**（rev3 REVIEW §4、review 期補的守門：非 R_SUPER 的 desired⊄effective→`2222 grantExceedsOwn`）——v1 casbin 寫端 seed 即 R_SUPER-only、結構性不可達；**延後＋BACKLOG 立條**（下放前必建，見 §8）。
- rev3 的牆鐘 restorability 判定（被 role_id 取代）、reason 過濾器 defer 姿態（本刀做齊）。

---

## 事實地基（2026-07-11~12 偵察、關鍵處逐 file:line 核實）

- **schema 全套已在 002 凍結基線、本刀唯一結構變更＝m007 加一欄**：`sys_role`（六審計欄＋`status smallint`＋`role_code/role_name/role_memo/role_home/role_desc`；partial-uniq `sys_role_code_active_uniq (role_code) WHERE deleted_at IS NULL`）、`sys_user_role`（PK(user_id,role_id)、雙向 FK **RESTRICT**）、`casbin_rule`（11 欄含 `protected bool NOT NULL default false`＋`created_at/created_by`；uniq `(ptype,v0..v5)`）、`sys_casbin_policy_archive`（`archive_reason varchar(32)`＋原列快照欄＋`archived_at/by`；索引 `idx_casbin_archive_role_dim (v0,v2)`；**無 role_id 欄**→B-034 落點）、`sys_menu`（含 `buttons jsonb`、`i18n_key`、route_name partial-uniq）。出處＝docs/generated/reference/schema.md（實庫快照）。
- **casbin seed＝149 列全 p 型、零 g 型**（user→role 走 `sys_user_role` 表；85 menu／23 GET／18 POST／7 DELETE／16 button）；**本刀 20 端點的政策全數已預埋**（`specs/002-schema-baseline/fixtures/json-casbin_rule.json`），含 `deleteRole`／`batchDeleteRole` 動詞＝**DELETE**；**19 列 protected=true**＝治理面恢復路徑（getRoleMenu/updateRoleMenu、getAllButtons/getRoleButton/updateRoleButton、getAllEndpoints/getRoleEndpoints/updateRoleEndpoints、getDeletedMenus/restoreMenu、getSystemSettings/updateSystemSetting、updateUserSessionPolicy、getArchivedPolicies/restorePolicy＋manage_role/manage_menu/manage_system-settings/manage_policy-archive 選單）。button code `role:add/edit/delete` 已 seed（`sys_menu.buttons` jsonb＋casbin button 列）。
- **讀端政策差異**：`getRoleList`／`getUserList`＝R_SUPER＋R_ADMIN；`getAllRoles`＝三角色全授；其餘 role 域端點 R_SUPER-only。
- **seed 三角色**：R_SUPER(1)／R_ADMIN(2)／R_USER_COMMON(3)，`role_name` 為簡中 demo 值（「超级管理员」等）、`role_home='home'`、`status=1`。
- **後端現況**：role 域端點**零**（reference/routes 僅 auth/route/systemManage-settings/ip-rule/unlockLogin）；`require_policy`＝DB-fresh roles→`enforce_role_path_method`（`server/src/auth/enforce.rs:178-198`）；enforcer＝`Arc<RwLock<Enforcer>>`（`state.rs:35`）——寫端 write-lock `load_policy()` 全量重載的口現成；`roles_of_user` **只濾軟刪、不濾 status**（`model/facade/sys_user_role.rs:37-48`）→ 停用角色現況仍授權（D6 拍板改）；`get_user_info` 已回 buttons（casbin `act='button'` 枚舉、`handler/auth.rs:714-733`）——**button 維讀半邊 005 已建好**；`getUserRoutes`＝DB-fresh roles→casbin 枚舉 `act='menu'`→`sys_menu` list_active→祖先包含組樹→`{routes, home}`（活書 §6）。
- **寫端範式現成（008 先例）**：facade `mutate_in_txn(Op)`＋op-log 同 txn（`model/facade/sys_ip_rule.rs:156`、`handler/ip_rule.rs` 四寫端恰四列 op-log 測試）；partial-uniq 23505→`2222` Conflict；notFound→`2222` 不靜默；**`HttpMethod::Delete` 已入 router**（`router.rs:30`、rev4 首條 DELETE 路由＝deleteIpRule）——deleteRole/batchDeleteRole 動詞零阻力。migration 序＝m001~m006 已用、**本刀＝m007**。
- **前端現況**：manage/role 頁模板全套（index＋role-operate-drawer＋role-search＋menu-auth-modal＋button-auth-modal）；讀側已呼叫（`fetchGetRoleList` index:23、`fetchGetAllPages` menu-auth:44、`fetchGetMenuTree` menu-auth:63——後端端點不存在、現況必敗）；**寫側全 stub**（index delete:125/batchDelete:118、drawer submit:86、menu-auth getHome:29/updateHome:35/getChecks:72/handleSubmit:78、button-auth 三 stub）。**home 選擇器＝upstream 模板既有 UI**（menu-auth-modal template L104-105）——接線＝補完 placeholder、與同 modal 其他 stub 同一授權基礎（D3 前提更正的關鍵事實）。`hasAuth` 讀 `authStore.userInfo.buttons`（`hooks/business/auth.ts:12-15`）。
- **wire 凍結形**（`typings/api/system-manage.d.ts`＋`common.d.ts`、不動）：`Role`＝`CommonRecord<{roleName,roleCode,roleDesc}>`；`CommonRecord`＝`{id:number, createBy:string, createTime:string, updateBy:string, updateTime:string, status:'1'|'2'|null}`；`RoleSearchParams`＝`RecordNullable<Pick<Role,'roleName'|'roleCode'|'status'> & {current,size}>`；`AllRole`＝`Pick<Role,'id'|'roleName'|'roleCode'>`；`RoleList`＝`PageRes<Role>`；`MenuTree` 已有型。button／endpoint／archive 新形→ADAPT 新 `.d.ts`；新 fetcher→WRAPPER `rev4-*.ts`（凍結的 `system-manage.ts` 不動）。
- **選單 seed 現況**：78 條；manage 子樹＝user/role/menu/user-detail/system-settings/policy-archive（protected）＋audit/ip-rule（非 protected）；`manage_policy-archive` 選單項與政策已 seed、**缺的只是三語譯文＋頁面**（B-061）。

---

## 拍板紀錄（2026-07-11~12，user 逐題親決）

| # | 議題 | 拍板 |
|---|---|---|
| D1 | endpoint 授權維度（rev3 016 自建維、模板沒有） | **進 009**：三端點＋net-new endpoint-auth-modal（MODAL-WIRING (c)）；casbin 寫端底座一次建好、三維都是消費者 |
| D2 | 回收桶頁 manage/policy-archive | **進 009**：getArchivedPolicies＋restorePolicy＋新頁（MODAL-WIRING (e)）＋`route.manage_policy-archive` 三語（B-061 三清一） |
| D3 | roleHome 編輯 | 初問拍延後（前提＝嵌 modal 有 Amendment 風險）；**查證後前提更正**（home 選擇器＝upstream 既有 UI、接線＝placeholder 補完）**重問改拍進 009**——延後反而留下「切了彈回」的靜默 no-op 死控件（K2-09 型縫隙） |
| D4 | B-060 demo 選單清理 | **不進 009**：留 menu 頁刀或獨立清理刀；demo 選單當 casbin 下放測試素材 |
| D5 | B-034 archive 加 role_id 欄 | **加**（m007、nullable、指向來源 `sys_role.id`、**不設 FK**）；此刻不加＝舊歸檔列永遠 NULL、判定退化 |
| D6 | 停用角色（status='2'）授權語意 | **A 案停用即斷權**：`roles_of_user` 加 status 活性濾→下一請求即生效（選單收縮、Policy 端點 5003）；連動 self-guard（不可停用自己所屬角色） |
| D7 | B-047 拒因訊息粒度 | **②結構化明細案**：distinct i18n key＋`2222` 信封 **`data` 欄**載插值參數（如「掛著 3 個使用者”）；洩漏評估入 ADR |

---

## §1 總覽：一台治理狀態機、五個施工分段

```
P0  m007 migration（archive.role_id）＋停用斷權（roles_of_user status 濾＋既有測試連動改寫）
P1  B-047 明細通道地基（AppError 攜參變體→2222 data 欄）＋sys_role facade 擴充
    ＋role CRUD 六端點（三層守門、批次自管 txn no-partial）
P2  casbin 治理核心（set_role_dimension／set_role_endpoints／insert_archived／reload-on-Applied）
    ＋三維讀寫端點＋支撐讀（getMenuTree／getAllPages／getAllButtons／getAllEndpoints）＋roleHome
P3  回收桶（getArchivedPolicies 分頁雙濾＋restorePolicy 三態＋role_id 同實例判定）
P4  前端接線（MODAL-WIRING (a)(b)(c)(e)＋ADAPT/WRAPPER）＋i18n 三語＋CDP 實機驗收
```

依賴方向單一：P0→P1→P2→P3→P4（P2/P3 共用 insert_archived；P4 消費全部）。全新寫（RUSTAPI-SOURCE-ISOLATION），rev3 實碼只作機理參照。**20 端點全數已 seed、政策零遷移**；router 註冊動詞必須逐條對齊 seed act（GET/POST/DELETE）。

## §2 role CRUD（P1）

- **getRoleList**（R_SUPER＋R_ADMIN）：`PageRes<Role>`；濾 roleName（模糊）／roleCode（模糊）／status（等值）；預設排序 id asc（列表排序掛載＝B-036 獨立刀、不進）。wire 映射：`status` smallint 1/2 ↔ `'1'|'2'`；`createBy/updateBy`＝audit 欄 id 字串化（UI 不消費、誠實填值不 join）；`createTime/updateTime`＝ADR 0002 形。
- **getAllRoles**（三角色全授）：活性＋啟用（status='1'）角色的 `AllRole[]`——typings 註解明言「these roles are all enabled」；user 頁刀（B-064 族）前置。
- **addRole**：`{roleName, roleCode, roleDesc, status}`；role_code 守門＝非空＋形制白名單（`^[A-Za-z0-9_]+$` 類、防 casbin v0 注入分隔符——確切 regex spec 期定）；重複 active code→23505→`2222 biz.role.codeExists`；**新角色零授權起步**（menu/button/endpoint 全空、經三 modal 下放）。
- **updateRole**：**role_code 不可變**（變更請求→`2222 biz.role.codeImmutable`）——casbin v0 恆穩、零 cascade rename、archive 對應不撕裂；可改 roleName／roleDesc／status；**全 None 提前 no-op**（B-050：不 bump 時戳、不寫 op-log）；roleDesc 送空字串＝清空（B-026 完整解留部分更新 wire 刀）。status 改停用→self-guard（§4）。
- **deleteRole／batchDeleteRole**（DELETE 動詞、對齊 seed）：三層守門→軟刪＋同交易 `archive_all_role_policies`（§4）；批次**自管 txn**（B-049、不借 sentinel DbErr）＋逐項驗證整批拒 no-partial。
- 全寫端沿 008 範式：facade `mutate_in_txn`（op-log 同 txn、逐欄快照）＋handler 守門前置。

## §3 casbin 授權治理狀態機（P2 核心）

1. **全量替換**：前端送 desired 全集→後端讀 current→diff→to_revoke＋to_grant。
2. **DB-first**：同一交易內直寫 `casbin_rule`（DELETE＋INSERT）＋op-log；絕不走 enforcer MgmtApi 寫面。
3. **protected-reject**：to_revoke 含 `protected=true` 列→整批 Rejected、零變更（在任何寫之前）、`2222 biz.policy.protectedRevoke`＋data 明細（§5）。
4. **revoke＝archive-move**：快照→INSERT `sys_casbin_policy_archive`（**帶 role_id**、reason=撤銷類 distinct 值）→DELETE live——誤撤可經回收桶自助復原；**grant＝INSERT**（`protected=false`＋`created_at/created_by` 治理欄補寫）。
5. **競態防護**：casbin 寫端（updateRoleMenu／updateRoleButton／updateRoleEndpoints）**＋restorePolicy**與 deleteRole／updateRole 改 status 同交易 `SELECT … FOR UPDATE` 鎖該 `sys_role` 列（grant-during-delete 鎖序）。★**對抗式審查 Blocker 1（2026-07-12）修正**：restorePolicy 原漏出鎖序集——它同屬「向 casbin_rule 寫 live 列」的 grant 型寫端，其 `restorable`（角色活性＋同實例）若為無鎖預讀、與 deleteRole 交錯即 TOCTOU：restore 讀到刪除前的活性快照判 restorable→INSERT，delete 的 archive-all 快照早於該 INSERT→漏掃→軟刪後殘留一列 live `v0=role_code`，被同 code 重建角色靜默繼承（違憲法 §B2 lock-then-redecide、FR-011／FR-012）。修法：restorePolicy 同交易 `SELECT sys_role WHERE role_code=archived.v0 AND deleted_at IS NULL FOR UPDATE`，**鎖內重驗** restorable（角色不在→拒 `notRestorable`）後才 INSERT，23505 比照 addRole 收斂 `2222`，與其餘 casbin 寫端共用同一鎖序。
6. **reload-on-Applied**：txn commit 後 Applied（含空 diff）→ `enforcer.write().await.load_policy()` 同步全量重載；Rejected/NoOp/NotFound→skip。**跨副本門鈴不做**（enforcer＝行程內狀態、單副本部署下 pub/sub 是死路徑；隨 B-038 多副本刀）。★**對抗式審查 Blocker 2（2026-07-12）修正——reload 失敗契約**：原設計 commit 後 `load_policy()` 無任何失敗處置。casbin `load_policy` 疑為 clear-then-load（先清 in-memory model 再由 adapter 載入，`?` 於載入前早退即留空 model；此機制 plan 期須對 crate 實碼核實）——一次暫時性 DB 失敗即清空 in-memory 政策→其後每個 `require_policy` 對含 R_SUPER 的全體角色一律 `5003`、救援端點（getArchivedPolicies／restorePolicy 皆 Protection::Policy）亦被封死→**全域授權鎖死、唯重啟可恢復**（違 FR-018 防鎖死 by-design、Assumptions「超管永遠改不掉自己的修復入口」、ADR 0044 降級必告警）。修法：**保留上一份已知良好 in-memory 快照**（載到暫存成功才 swap、不裸 clear-then-load）＋結構化告警＋有界重試；沿既有「保留已知良好」降級範式（008 FR-018）與授權面 fail-closed 紀律（`auth/enforce.rs` denylist Err→PG fallback）；補一條 reload-failure 負向測試與留痕。
7. **facade 形**：`set_role_dimension(txn, role_code, dim∈{menu,button}, desired, meta, role_id)`（v2 固定值）＋`set_role_endpoints(txn, role_code, desired:&[(path,method)], meta, role_id)`（current 辨識＝HTTP method 白名單）。
8. **menu 維映射**：wire 收 menu id `number[]`→`sys_menu` 活性表轉 route_name（orphan skip）→casbin v1；讀端反向。
9. **registry 真源**：getAllEndpoints＝ROUTES const 過濾 `Protection::Policy`（含 path＋method）；getAllButtons＝`sys_menu.buttons` jsonb 聯集（活性選單、去重）。
10. **生效延遲語意（明文設計事實）**：API 強制每請求 DB-fresh→**即時**；前端選單／按鈕顯隱要等下次 `getUserRoutes`／`getUserInfo`（app 重載）——不做推播、文檔明示。

## §4 刪除・停用・復原（狀態機的三個危險面）

- **deleteRole 守門（序固定）**：①seeded（hardcode `R_SUPER/R_ADMIN/R_USER_COMMON`，sys_role 無 protected 欄、零 migration）→`2222 biz.role.seededProtected`；②in-use（`sys_user_role` 有指派）→`2222 biz.role.inUse`＋data `{userCount}`；③self-role（操作者所屬角色）→`2222 biz.role.cannotDeleteSelfRole`。過門→軟刪＋**同交易全維歸檔**（含 protected 列、reason=`role_soft_delete`）→reload。三 seeded 角色實測皆 in-use（雙重守）。
- **停用斷權（D6）**：`roles_of_user` 加 `status=1` 活性濾——單點改動、RBAC 判定鏈／getUserRoutes／getUserInfo buttons 全下游生效；self-guard＝不可停用自己所屬角色→`2222 biz.role.cannotDisableSelfRole`；**R_SUPER 恆禁停用**（結構護欄：v1 操作者必掛 R_SUPER、self-guard 已隱含擋下；顯式規則防「role CRUD 端點下放後、非 super 停用 R_SUPER」的複合路徑——該 policy 列非 protected、下放技術上可達）。既有消費者連動核對（getAllRoles 語意本就要求 enabled）。
- **restorePolicy 三態＋同實例判定（B-034 兌現）**：`restorable` ＝ reason≠`role_soft_delete` **且** 現存同 code 活角色 `id == archived.role_id`（同實例；去牆鐘化、同時封死「經 restore 把舊實例授權灌進同 code 新角色」的繼承旁路）；menu 維另驗 target route_name 活性（orphan→`2222`、不灌無效列）。可復原→反向 move＋op-log；已 live→NoOp `0000`；假 id／不可復原→`2222`（`biz.policy.notRestorable`）。★**restorable 判定與 INSERT 同交易、鎖內重驗**（§3-5 鎖序、對抗式審查 Blocker 1）——`FOR UPDATE` 鎖 `role_code=archived.v0` 之活角色列後才重判＋寫入，杜絕 restore-during-delete 競態的無鎖預讀破口。
- **回收桶列表**：`PageRes` 分頁＋來源角色濾（role_id）＋維度濾（v2 推導）；`restorable` 隨列下發、前端 false 顯停用態。

## §5 B-047 ②結構化明細通道（D7 拍板）

- **載體**：business error（HTTP 200、`code:"2222"`）的 **`data` 欄**載該 i18n key 的插值參數物件——信封三欄不增不減、`data` 型別本就逐端點自由；**plan 期 Constitution Check 正式驗證此讀法不觸 §I.3 Amendment**。
- **形**：`msg`＝distinct key（`biz.role.seededProtected`／`inUse`／`cannotDeleteSelfRole`／`cannotDisableSelfRole`／`codeImmutable`／`codeExists`／`biz.policy.protectedRevoke`／`notRestorable`…）；`data`＝參數物件（`{userCount:3}`、`{blocked:[{target,dimension}…]}`）；前端 `$t(msg, data)` 插值。
- **後端形**：AppError 新攜參變體（如 `Biz(key, Option<Value>)`）；既有無參 `2222` 路徑零改動。
- **洩漏評估**（入 ADR）：受眾＝R_SUPER（v1 寫端唯一可達角色）、內容＝其本可經 list 端點自查的資訊（被擋 policy 清單、使用者計數）→無新增洩漏面；若日後下放寫端，明細通道須隨 M-6 一併重評。
- **前端通道風險（spec 期第一查證點）**：soybean request 攔截器在非 `0000` 時是否把 `data` 帶到呼叫端；若攔截器丟棄，接法（局部 catch／攔截器帶欄）屬 §III 授權邊界議題、plan 期定。

## §6 前端接線（軌道對照）

| 接線 | 軌道 |
|---|---|
| role 頁 index（delete/batchDelete）／role-operate-drawer（add/update）stub 接真 API | MODAL-WIRING (a) |
| menu-auth-modal 四 stub（getChecks／handleSubmit／**getHome／updateHome**）＋button-auth-modal 三 stub | (a)——★plan Constitution Check 確認 (a) 文字（operate-modal/drawer＋index handler）涵蓋 auth-modal placeholder；rev3 同邊界已驗證、實質同紀律 |
| 操作鈕 `hasAuth('role:add'/'role:edit'/'role:delete')` 顯隱 gating | (b)（讀半邊已活） |
| **endpoint-auth-modal net-new**（鏡像 menu/button modal；path 群組樹、`NTree check-strategy=child`＋synthKey——rev3 坑帶防）＋觸發鈕＋i18n key | (c) |
| **manage/policy-archive 新頁**（嚴格鏡像 manage 範式：search＋table＋分頁；restore 操作欄、restorable=false 停用態）＋route＋i18n key | (e) |
| `route.manage_policy-archive` 三語譯文（隨建頁走、B-061 三清一） | (e) 內含 |
| role-search reset 鈕補 `emit('search')`（沿 rev3 2026-07-02 拍板：清完自動重查、對齊全站慣例） | (a) 鄰接補完——★plan 期以「補完 vs 新能力」四條件覆核、不 bump 憲法 |
| 新 typings（button registry／(path,method)／ArchivedPolicy）＋新 fetcher | ADAPT 新 `.d.ts`＋WRAPPER `rev4-role-admin.ts` 等新檔；凍結檔不動 |

i18n 紀律：`App.I18n.Schema` 先擴、三語 locale 同 commit（否則 raw key 洩漏）；新 key 後 restart base-web 再 CDP（L-015）；`.vue` template 內 fork-delta 標記用 `<!-- -->` 形（L-119）；base-web commit 一律 `--no-verify`。

## §7 測試與驗收

- **rust**（容器內、全程 serial）：facade／handler 單元＋整合；治理狀態機 table-driven（diff 正確性、protected-reject 零變更、archive-move 快照完整、reload-on-Applied 含空 diff、method 白名單辨識、id↔route_name orphan skip、FOR UPDATE 鎖序）；**每條新 route 契約 case**（coverage gate 強制、20 條）。
- **負向自證**（證守門非恆綠，比照 007/008 傳統）：①拆 protected-reject→整批拒測試須 FAIL；②拆 self-guard（delete＋disable 兩路）→自鎖測試須 FAIL；③restore 判定去掉 role_id 同實例比對→「同 code 重建後舊列不可復原」測試須 FAIL；④batch no-partial 改逐項提交→「批內一項違規整批零變更」測試須 FAIL。
- **CDP 實機**（rev3 定論 curl≠modal；L-121~123／L-131／L-135 紀律）：role CRUD 全鏈（新增→編輯→刪除→批刪擋拒）；三 auth-modal 真打（勾選→提交→重開驗回讀）；roleHome 切換；回收桶列表雙濾＋restore＋不可復原停用態；**換角色登入驗選單／按鈕收縮**（casbin 下放即時性、demo 選單當素材）；停用斷權即時性（Policy 端點 5003）；B-047 明細插值顯示。
- **收刀閘**：`cargo test --workspace` 全綠；`pnpm typecheck`＋`tools/fork-delta-lint` 綠；docs-sync `refresh`＋`generate`＋三 lint 閘綠；m007 走 gate1 structural additive 白名單＋同 commit（L-109）。

## §8 治理（憲法動作清單）

- **新行為島 G（casbin 授權治理）進場**（MINOR Amendment、plan 期定稿）：G1 DB-first 寫入（直寫規則表＋同交易 op-log、絕不 MgmtApi 寫面、寫後全量重載）；G2 protected-reject（撤及 protected→整批拒零變更；un-protect 經 UI 不做）；G3 revoke 必歸檔（含刪角色全維連動、reason 區分、role_soft_delete 不可手動復原）；G4 刪除三層守門＋批次 no-partial；G5 restore 同實例判定（role_id tiebreak）。
- **ADR drafts（隨 SDD 落檔、user 親決）**：①治理狀態機總綱（G1~G5＋停用斷權 D6＋roleHome 語意）②B-034 role_id 欄（m007）③B-047 data 欄明細通道（含洩漏評估＋§I.3 讀法）。
- **BACKLOG 動作（收刀時）**：消化 B-034／B-047／B-049／B-050 全刪；B-061 amend（去 policy-archive 項、留 audit/ip-rule 兩項）；**新增**「M-6 no-escalation＋seeded 角色停用護欄複評——casbin 寫端或 role CRUD 端點下放非 super 前必建（desired⊄effective→拒；R_SUPER 禁停已本刀落）」。
- **錯誤碼**：全部 reuse `2222`／`0000`／`5003`，**零新碼**；新 biz key 走既有 i18n 軌道。
- **憲法 §I.2 兌現註**：本刀落地後「demo menu 可見性由角色勾選層治理下放」從 seed 靜態事實變成 runtime 可操作（updateRoleMenu）。

---

## 已知風險與遺留

1. **前端 data 通道未接地**：B-047 明細依賴攔截器把 `data` 帶出——spec 期第一查證點；若通道需動攔截器＝§III 授權議題（plan 拍）。
2. **role CRUD 政策非 protected**：updateRole/deleteRole/addRole 的 seed 政策列 protected=false——R_SUPER 技術上可下放給 R_ADMIN；配合 M-6 未建＝複合風險（已以 R_SUPER 禁停護欄＋BACKLOG M-6 條目圍堵；下放本身 v1 無 UI 誘因）。
3. **停用斷權的 UI 生效延遲**：API 即時、前端選單/按鈕等下次 app 重載——明文設計事實（§3-10）、不做推播。
4. **seed role_name 為簡中 demo 值**：「超级管理员」等屬 002 凍結 fixture、本刀不改 seed（撞 gate2）；admin 可經 updateRole 改 roleName（runtime 資料、非 code）。
5. **回收桶同 policy 多列**：同一 policy 反覆撤銷會累積多列歷史——restore 的「已 live→NoOp」語意天然容納；列表以 archived_at desc 呈現。
6. **本刀規模**：20 端點＋一 migration＋一新頁＋一新 modal，預估 12~16 執行單元、近 007/008 先例；編排照 CLAUDE.md §2（防呆五件套＋看門狗原子成對＋單元邊界 pin bump；`wf-watchdog RUNAWAY=25` 按 TDD 單元寫死、fan-out 型先估 journal 行數）。
7. **對抗式審查已跑（2026-07-12、clarify 後補跑）**：7 鏡頭×3 異質核驗，抓 2 blocker（restore 未納鎖序、reload 無失敗契約）全數折入 spec＋本檔、1 CONTESTED（活書 §6 as-built）走收刀通道——紀錄詳下方§對抗式審查紀錄。
8. **M-6 延後的射程**：v1 唯一寫端角色＝R_SUPER（effective＝全集、no-escalation 空言）；任何下放動作觸發 BACKLOG 條目回收。

---

## 對抗式審查紀錄（2026-07-12，clarify 後補跑；008 範式）

**編排**：Workflow 7 鏡頭（權限提升／併發競態／狀態機不變式／鎖死可用性／資料完整性遷移／資訊洩漏／憲法紀律 scope）獨立掃 → 每 finding 3 異質核驗者對抗式駁斥（事實核／已緩解核／可達性核）→ barrier 去重綜合。看門狗 fan-out 型原子成對。統計：raw **32**／CONFIRMED **4**／CONTESTED **2**／REFUTED **26**（26 條經多票駁回，多屬「已被既有 FR/拍板緩解」或「結構性不可達」）；104 agent、8 核驗票 StructuredOutput 重試耗盡（分散於被駁條，未架空任一存活議題判定——2 blocker 各 6 票、CONTESTED 1:1）。

**Blocker 1（CONFIRMED、六票零實質反駁、跨 3 鏡頭同指）— restorePolicy 未納入 FOR UPDATE 鎖序**：
restore-during-delete 競態下，無鎖預讀判 restorable 後才 INSERT，使一列現役授權逃過刪除連動歸檔而殘留、被同代碼重建角色靜默繼承。**違已入憲 §B2「lock-then-redecide、永不信 pre-read」（L-075）＋FR-011／FR-012／SC-004**。→ 折入 §3-5 鎖序＋§4 restorePolicy＋spec FR-022／FR-030／SC-007／SC-012。**處置＝修入 spec（工程正確性＋憲法兌現，非新拍板）**。

**Blocker 2（CONFIRMED、4:2、跨 2 鏡頭同指）— reload-on-Applied 無 load_policy 失敗契約**：
commit 後 `load_policy()` 失敗無處置；casbin 疑 clear-then-load，一次暫時性 DB 失敗即清空 in-memory 政策→含 R_SUPER 全域 fail-closed 鎖死、救援端點亦封死、唯重啟可救。**違 FR-018 防鎖死 by-design＋ADR 0044 降級告警**。方向歧見（stale-allow vs 鎖死）經核驗票收斂為「clear-then-load 鎖死」（機制 plan 期須核 crate 實碼）；修法「保留上一份已知良好快照＋不 clear-then-load＋告警＋有界重試」對兩方向皆正確、且沿 008 FR-018 與 `enforce.rs` 既有 fail-closed 範式。→ 折入 §3-6＋spec FR-021／SC-013。**處置＝修入 spec**。

**CONTESTED（1:1）— 活書 ARCHITECTURE §6「home＝角色首個非空 role_home」as-built 失真**：
事實成立（FR-039 讀端兜底後 §6:139 逐字敘述變不完整、活書權威高於 spec）；但 refuter 有力——提議「入 tasks」撞 rev4 `livedoc-asbuilt 歸收刀、不排進 feature branch`紀律（撞 docs-sync L6(b) 閘）。synthesis 判「已緩解-澄清」：**走收刀 arch-impact 通道**更新活書 §6（＋補生效延遲語意落點）、不入 tasks，與 005 spec 勘誤並列。已記入 spec 治理節「前刀 as-built 勘誤＋活書更新」。此收刀分工提請 user 知悉。

**未升級為 finding 的健壯度確認**（26 駁回中的代表）：deleteRole 三層守門＋FOR UPDATE、protected-reject 零變更、in-use 疊種子雙重守、endpoint method 白名單辨識、B-047 明細受眾邊界、行為島 G 進場——經核驗確認已被既有 FR/拍板覆蓋或結構性不可達。
