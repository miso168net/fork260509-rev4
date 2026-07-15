# Quickstart 驗收: 011-user-admin

**Branch**: `011-user-admin` | **Date**: 2026-07-13 | **Plan**: [plan.md](./plan.md)

端到端驗收指南（非實作碼）。rust 單元／整合＝容器內 `cargo test --workspace`（serial、host 無 toolchain）；前端互動＝CDP 實機（curl≠modal，rev3 定論）。端點 wire 契約（9 新 fetcher〔getUserList 複用凍結〕／DTO 形、DELETE 動詞、body `{id}`/`{ids}`）見 [contracts/user-admin-endpoints.md](./contracts/user-admin-endpoints.md)；實體、統一鎖序與守門矩陣見 [data-model.md](./data-model.md)——本檔不重複契約與模型內容，只列**驗收動作與預期**。前置＝rev4 stack 起（前端 `:42080`、乾淨 DB）＋**m008 seed-only migration 已 migrate**＋**憲法島 I（使用者域治理）五條**：draft 先行、後端執行單元按 draft 施工、**accepted 於前端執行單元前**（T029 user 親決；驗收時 v1.9.0 已入憲）。

本刀觸及既有 auth 流程（`run_login`/`run_refresh`，005/006 碼）——並發機器證第 4 組為 load-bearing，實作與測試須格外謹慎。

## 前置

```
# 容器內、serial（host 無 toolchain；平行 cargo 互撞 target）
docker compose exec rust-api cargo test --workspace   # 全綠含 10 端點契約 case＋守門矩陣負向＋密碼政策 7 鍵矩陣＋併發機器證
docker compose exec rust-api sh -c 'ls migration/src/m008*'  # m008（seed-only、8 列 casbin_rule）存在
grep -n '島 I' .specify/memory/constitution.md              # v1.9.0 已入憲（使用者域治理五條 I1~I5）
# 前端：base-web vite dev server 於 :42080（乾淨 DB）
# CDP：Edge@9229 WebSocket、quick-login（rev4-cdp 速查：localStorage·i18n·toast 取用）
# ★新 i18n key（backend.biz.user.* / backend.biz.unlock.* / page.manage.user.*）後 restart base-web 再 CDP（L-015/L-114）
```

## 全量閘清單（收刀閘）

- `docker compose exec rust-api cargo test --workspace` 全綠（含負向自證守門、密碼政策矩陣、併發機器證）。
- **gate2**：凍結定稿 244 列全 present＋**m008 新增 8 列走 `SEED_ADDITIVE_ALLOWLIST` 容差 extra**（4 端點 p 列＋4 按鈕碼 user:kick/user:reset-pwd/user:restore/user:unlock、全授 R_SUPER）、**fixtures 零改寫**（byte 級原樣）；m002 一字不動、零 schema 變更（零建表零加欄）。
- `pnpm typecheck` 綠（i18n 三範圍 Schema 型與譯文同 commit、L-094）。
- `tools/fork-delta-lint` 綠（**基線 example@8be6f9ba**；base-web 修改型檔 `index.vue`/`user-operate-drawer.vue`/登入頁 `pwd-login.vue` 逐行含 `原行:`；新檔 `rev4-user-admin.ts`/`.d.ts`/`user-unlock-modal.vue` 走新增型零原行）。
- `tools/docs-sync check`（generate＋三 lint 閘）綠；m008 走 gate1 結構白名單＋同 commit（L-109）。
- 憲法 v1.9.0＋ADR-a/b/c accepted；活書 §6 as-built 更新走收刀 arch-impact（不入 tasks）。

## CDP 實機場景

CDP 建列場景（新增／刪除／重建）用測試專屬 `userName` 前綴、跑完精確清理＋**順跑 gate2**（L-138；本刀零 seed fixtures 變更、gate2 應全綠、僅 m008 走容差 extra）。

### S1 使用者 CRUD 全鏈＋政策拒因＋會話策略（US1／US5）
1. 進 `/manage/user`；列表載入（`fetchGetUserList` 200、非現況必敗；含 `userRoles`（code[]）與 `session_policy` 欄；**回應 MUST NOT 含 password 雜湊與 session_id**，SC-002/SC-009）。
2. 搜尋欄留空（送空字串）→ 空字串等同未設（不整頁落空、數字欄空字串不致 400；FR-001，沿 009 L-089/L-090）。
3. 新增合法帳號名／初始密碼／基本資料／角色 → 成功；同**活性**帳號名重複 → `2222 userNameExists`；弱密碼未過政策 → `2222 passwordPolicy`＋違規清單明細。
4. 帳號名重用：以**已軟刪**帳號名新增 → 成功（帳號名可重用；SC-003）。
5. 編輯：改 nickName/userGender/userPhone/userEmail/status/userRoles → 成功；帳號名欄 edit 模式 **disabled**（雙保險）＋繞 UI 直送變更 → `userNameImmutable`（B-025 後端半、FR-006）。可空字串欄送空＝清空、user_gender 不提供清空語意（B-026 部分）。
6. 空 diff 提交（未攜任何欄位變更）→ 提前 no-op：不更動時戳、不落 op-log（FR-007）。
7. 角色指派清單含未知／已刪 role code → `roleNotFound` **整批拒**（不靜默丟棄；FR-008）。指派變更「提交→重開回讀」一致；以受影響帳號實際登入，選單／按鈕／API 可達性對齊（SC-002）。
8. **session_policy select**（edit 模式）以真實現值渲染（讀取通道存在、不以預設值渲染致 diff 誤判弱化他人策略；FR-034）；改值提交獨立 `updateUserSessionPolicy`，該帳號**下次登入**依 per-user 覆寫優先於全域生效（改 single 不即時踢、下次登入收斂；FR-035／SC-011）。
9. 刪除 seed 帳號（id∈{1,2,3}）→ `seededProtected`；刪自己 → `cannotDeleteSelf`（FR-010）。
10. 通過守門刪除 → 軟刪除（成對寫 deleted_at/by）＋**同交易硬刪 sys_user_role 指派列**＋撤該帳號全部 session；op-log 同交易落地、payload **不含密碼**（FR-012）。
11. 批次刪除含一違規（含已刪識別）→ **整批拒、資料零變更**（fail-fast；FR-011／SC-001）。

### S2 停用／踢除／改密即時斷線（US2／US3、雙瀏覽器 session、8888/7777 分流）
1. 雙瀏覽器（或雙 profile）以測試帳號 T quick-login 建兩條 session（sid_A/sid_B）。
2. Super 停用 T（`updateUser` status 1→2）→ 兩 session 下一受管制請求於失效廣播後被拒（**8888 靜默登出**）；換發亦被既有活性守門擋（FR-014）。
3. 停用後重新啟用 T → 既有 session 已撤、須重新登入方能存取（語意自洽；US2-7）。
4. Super 踢除 T（`kickUser`）→ 兩 session 呈**阻斷式「已被登出」modal（7777）**；帳號仍啟用、可重登（FR-015）。
5. Super 對 T `resetUserPassword`（T≠operator）→ 舊 session **8888 靜默**、新密碼可登入；持舊密碼者並發登入被登入鎖內活性／密碼重驗擋（不留漏網 session；FR-023/FR-025）。
6. operator 對**自己**重設密碼 → 其他 session 被撤、**當前操作 session 保留**（不自斷；FR-025）。reset 成功 toast 帶「若該帳號登入鎖定中需另行解鎖」指引（reset 不解節流；FR-025）。
7. self 守門：踢除／刪除／停用自己 → `cannotKickSelf`／`cannotDeleteSelf`／`cannotDisableSelf`（FR-016）。
8. Super（id=1）停用 → `superCannotDisable` 拒；踢除 → 允許（無永久傷害、可重登；FR-017／SC-006）。
9. 被合法撤銷（停用／刪除／改密）者持既有換發憑證換發 → **靜默 8888 拒、不落 reuse 稽核事件**（`run_refresh` revoked 分支；FR-020／SC-004）。

### S3 回收桶 toggle-restore 零回灌（US4）
1. NSwitch「顯示已刪除」ON → 列表改呈已軟刪使用者（**deleted_at 新到舊**）、operate 欄換 restore 鈕、隱藏 add／batchDelete；OFF → 回未刪列表（FR-030）。
2. restore 可復原列（無活性同名）→ 回活性列表、**零角色指派**（復原不回灌、須 super 重指派）、狀態保留刪除前原值（停用時被刪→復原後仍停用；FR-032／SC-010）。
3. restore 有活性同名 → `userNameExists` 拒（鎖內重驗＋partial-uniq 唯一約束兜底；FR-031／SC-003）。
4. restore 不存在識別 → `userNotFound`（不靜默；FR-031）。
5. 回收桶相關三語譯文齊、無 raw key（FR-033）。

### S4 解鎖 modal 雙維（US6）
1. header「解鎖」鈕（`user:unlock` 碼、hasAuth 顯隱）→ modal 呈 dimension select（帳號維／IP 維）＋目標輸入（FR-036）。
2. 帳號維：對登入鎖定中帳號解鎖 → 該帳號可再登入（解鎖冪等；SC-012）。
3. IP 維：合法位址 → 該 IP 段解除；非法／缺目標 → 專屬訊息（FR-036）。
4. 非 super 呼叫 `unlockLogin` → `5003` 權限拒因（super-only、007 已活）。
5. `backend.biz.unlock.*` 三語齊、無 raw key（007 欠帳補建；FR-037）。列表**不顯鎖定態**（權威態在快取、非資料欄；FR-036）。

### S5 拒因 i18n 三語零 raw key（US7）
逐一觸發各拒因（`seededProtected`／`cannotDeleteSelf`／`superCannotDisable`／`cannotDisableSelf`／`superRoleProtected`／`cannotChangeSelfRoles`／`cannotKickSelf`／`userNameExists`／`userNameImmutable`／`passwordPolicy`／`roleNotFound`／`userNotFound`＋`unlock.*`；勘誤 2026-07-15 B-088：原列 notRestorable 併歸 userNotFound、未發射）→ 各以**專屬訊息鍵**呈現（一因一鍵、含插值位、三語齊、無 raw key；FR-038/FR-040）；既有無明細業務錯誤路徑行為 100% 不變（FR-039／SC-014）。

### S6 密碼政策違規渲染（US3／US7、島 I5）
1. drawer add 模式密碼欄 → best-effort fetch 004 設定組動態 hint（「8–64 字、需數字…」）；fetch 失敗靜默降級為僅後端驗。
2. 提交弱密碼（短於 `min_length`／缺數字／缺大小寫／缺特殊字元）→ `2222 passwordPolicy`＋**具體違規清單明細**渲染（如「至少 8 字」「須含數字」；FR-026/FR-038／SC-007）。
3. 多位元組密碼超固定 bytes 上界（`LOGIN_PASSWORD_MAX_BYTES`=512）→ 拒（消滅「設得進、登不進」；FR-027）。
4. 密碼與帳號名相同（含大小寫變體）→ `forbid_username` **case-insensitive 相等**拒（不因大小寫繞過；FR-027）。
5. `resetUserPassword` 走**同一驗證點**、同明細（建帳／重設共用、零分叉；FR-026）。登入頁前端規則已放寬為 required-only（後端政策為唯一權威守門）。

## rust 併發機器證（≥4 組、SC-013／統一序列化域有效性）

以 `pg_blocking_pids`／`pg_locks`（`locktype='advisory'`）觀察後到者於域內等待；終態斷言＝二序列之一（等價某一先後序列）。

1. **`deleteUser` × `updateUser`（指派路）** 同一 uid 併發 → advisory_lock(uid) 序列化；終態無「已刪 user 殘留 live 指派」。
2. **`deleteRole` × `assignRoles`（updateUser 指派）** 同一 role 併發 → **B-084 兌現直接證據**：指派路鎖 sys_role 列升冪重驗活性、與 009 刪角色守門互斥；終態指派 × 刪角色守門不被繞過。
3. **`deleteUser` × `restoreUser`** 同一 uid 併發（濾條件互補：未刪 vs 已刪）→ 標的列鎖內重驗＋帳號名 partial-uniq 兜底；先提交者勝、另一方見不存在或衝突，無雙活性同名。
4. **★撤銷端點 × 並發登入**（B1 缺口、load-bearing）：停用／改密撤銷與並發 `run_login` 交錯 → login 於 advisory lock 內、insert token **前**重讀 sys_user 列並重驗 `status==1 && deleted_at IS NULL && password==authenticate 時所讀 hash`（純字串比對、不重跑 argon2），任一不符→中止 login 回 1000、不 insert token。斷言：**改密後以舊密碼並發登入 0% 殘留有效 session**（SC-005）。

## rust 負向自證（守門非恆綠、拆除即轉紅）

刻意拆除下列任一守門，對應測試**須轉紅**（各支防恆綠前置已烤進測試設計）：

1. **拆登入鎖內活性／密碼重驗**（`run_login` advisory lock 內重讀）→ 「並發登入 × 撤銷不留漏網 session」與「改密後以舊密碼並發登入 0% 殘留」轉紅（SC-005；★前置＝先建 session、改密後立即並發登入，確保有可漏網 session、防空集恆綠）。
2. **拆 seed 帳號守門**（deleteUser/batch seeded {1,2,3}；updateUser 停用路 `superCannotDisable`；指派路 `superRoleProtected`）→ 對應守門測試轉紅（SC-006；★Super 保護五道護欄逐支）。
3. **拆 self 守門**（刪除／停用／踢除三路）→ 自鎖／自斷測試轉紅（FR-016；標的用測試帳號、非 operator 自身以外之對照）。
4. **拆 batch fail-fast**（改逐項提交、非整批 rollback；或已刪 id 視為冪等跳過而非違規）→ 「批內一項違規整批零變更」轉紅（FR-011；★含已刪識別視為違規案）。
5. **拆 op-log payload 白名單**（payload 塞入 password/hash）→ 負向斷言「op-log payload 不含 `$argon2` 子串與 password 鍵」轉紅（B2；SC-008，trace_id 過濾 L-079）。
6. **拆 DTO Debug 遮蔽**（AddUserReq/ResetUserPasswordReq 改裸 `derive(Debug)`）→ 「除錯輸出不洩明文」斷言轉紅（FR-028；防 fix 迴圈誤加 `{:?}` 洩明文入容器 log）。
7. **拆 `forbid_username` case-insensitive**（改大小寫敏感相等）→ 「密碼＝帳號名大小寫變體被拒」轉紅（FR-027）。

## 驗收對照（15 SC → 佐證場景）

| SC | 佐證 |
|---|---|
| SC-001 CRUD 全鏈＋seed/self 守門＋batch 零變更 | S1(3-11)、負向 2/4 |
| SC-002 角色指派回讀一致＋登入可達＋未知 code 整批拒 | S1(7)、S2 登入驗收 |
| SC-003 帳號名重用＋復原同名衝突拒 | S1(4)、S3(3)、併發 3 |
| SC-004 停用/踢除/刪除/改密撤 session＋8888/7777＋換發靜默拒 | S2(2-9) |
| SC-005 並發登入 × 撤銷不留漏網＋改密舊密碼 0 殘留 | 併發 4、負向 1 |
| SC-006 Super 不可刪/停用/解超管指派＋恆 ≥1 活超管 | S1(9)、S2(8)、負向 2 |
| SC-007 密碼政策 7 鍵矩陣＋多位元組 bytes 上界＋弱密碼拒明細 | S6、負向 7、cargo 矩陣 |
| SC-008 密碼明文/雜湊 0% 出現於 payload/log/回應/錯誤 | 負向 5/6、S1(10) |
| SC-009 列表／回收桶回應不含 password/session_id | S1(1)、S3 |
| SC-010 回收桶三態＋復原後狀態保留原值 | S3 |
| SC-011 per-user session_policy 生效＋抽屜真實現值渲染 | S1(8) |
| SC-012 解鎖帳號維/IP 維生效＋非 super 拒＋三語 | S4 |
| SC-013 指派×刪角色、刪除×復原、撤銷×登入併發序列等價 | 併發 1/2/3/4 |
| SC-014 拒因明細＋三語＋無 raw key＋既有無明細路徑不變 | S5 |
| SC-015 零新錯誤碼＋零 schema 變更＋4 端點 4 按鈕增量種子＋凍結種子 0 改寫 | 全量閘 gate2、負向 5 |

## agent context

rev4 CLAUDE.md 為手維薄操作手冊（≤250 行 lint 強制），**不走 speckit auto agent-context 機制**——本步 N/A（009/010 先例；架構影響於收刀走活書 arch-impact＋docs-sync generate）。
