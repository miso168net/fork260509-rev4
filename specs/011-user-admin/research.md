# Phase 0 Research: 011-user-admin

研究決策彙整。格式：Decision / Rationale / Alternatives。上游＝brainstorm 13 拍板（D1~D13、user 逐題親決）＋6 鏡頭對抗式審查 25 findings 全折入；本檔聚焦「怎麼落地」的施工級決策（含 3 blocker 修正範式）。偵察事實來源＝2026-07-13 七路唯讀偵察（已對照實碼）。

---

## R1（B3）新增 seed 走 m008 顯式 migration，非改 m002

- **Decision**：4 端點政策（resetUserPassword／kickUser／getDeletedUsers／restoreUser）＋4 按鈕碼（user:reset-pwd／user:kick／user:restore／user:unlock）共 8 列 casbin_rule，由**新建 m008 seed-only migration** 顯式 INSERT（全授 R_SUPER）；同 commit 於 `tools/schema-gate` 的 `SEED_ADDITIVE_ALLOWLIST` 登記 8 項（key=(casbin_rule, natural_key)、註來源刀 011）；**m002 一字不動**。m008 無任何 schema DDL。
- **Rationale**：ADR 0032 §3 逐字要求「新增 seed MUST 由顯式 migration（非改 m002）落庫；凍結 fixtures 永不因新增 seed 改寫」。m002 為 run-once migration——已跑過 migration 的 DB（dev/staging/prod/持久 CI volume）其 `seaql_migrations` 已記 m002 applied，下次 `migration up` 跳過 m002，故加進 m002 的列**永不插入**→ 4 端點對 R_SUPER 全 5003 功能死亡（審查 B3 blocker）。m003/m005/m006 皆此範式（獨立 seed migration）。010 能「零 migration」是因其回收桶 seed 早預埋在基線 m002（偵察證：getDeletedMenus/restoreMenu 於 m002 命中 4）；011 四端點於 m002 命中 0（全新）。
- **Alternatives**：改 m002 直接加列——ADR 0032 明禁、run-once 下功能死亡，駁回。

## R2 使用者域寫端統一序列化域＝advisory_lock(uid)＋固定列鎖序（島 I1）

- **Decision**：一切使用者域寫端（含撤 session 者）於 txn 起手取 `pg_advisory_xact_lock(uid)`——**與 login/refresh 共用同一把鎖**。域內固定鎖序：①`sys_user` 標的列 `FOR UPDATE`（新 facade `find_active_by_id_for_update`；restore 用已刪列版 `find_deleted_by_id_for_update`）→ ②`sys_role` 列（僅指派路、id 升序、複用 009 `find_active_by_*_for_update`）→ ③`sys_user_role` 寫入。禁反向。
- **Rationale**：方案 1（列鎖＋固定鎖序、學 009）＝與資料形狀相稱——user 域每個寫端都有單一標的使用者列可鎖（平表、非 010 樹形需域鎖）。但對抗式審查（併發鎖序鏡頭）指出：純列鎖未納 sys_token 且與 login 反向取鎖（login＝先 sys_token〔revoke_others〕後 sys_user〔write_session_id〕；011 撤 session＝先 sys_user 後 sys_token〔revoke_all〕）＝ABBA 死鎖。**升級為 advisory_lock(uid) 統一序列化**：login 與 011 撤 session 皆以同一 advisory lock 為首鎖→完全序列化、消滅 ABBA 死鎖。與 009 鎖序（archive→sys_role→casbin/sys_user_role、不鎖 sys_user 列）無死鎖環（不同資源集）。
- **Alternatives**：方案 2 自立 user advisory 域（學 010）——把樹形不變式的成本搬到平表、過度武裝，且暗示「有跨列不變式要護」誤導後人，駁回（D12 user 親決方案 1）。純列鎖不納 advisory——ABBA 死鎖，駁回。

## R3（B1）並發登入漏撤修法＝login/refresh 鎖內重驗活性＋密碼 hash（島 I2）

- **Decision**：`run_login` 取 advisory lock 後、insert token **前**，於 txn 內**重讀** sys_user 列並重驗 `status==1 && deleted_at IS NULL && password == authenticate 時所讀 hash`（純字串比對、不重跑 argon2）；任一不符→中止 login（回 1000）、不 insert token。`run_refresh` 為 `revoked` reason 增「合法撤銷、靜默 8888、不落 reuse 事件」分支（對稱 kicked 的 7777 窄化）。★**換發側不重驗密碼雜湊**（FR-023 已收窄至 login 側）：login 側鎖內密碼重驗已堵「舊密碼 session 產生入口」，換發只延續已合法簽發的 chain；換發側漏撤保障＝既有換發憑證列鎖（`find_by_hash_for_update` FOR UPDATE）鎖鏈序列化＋活性 gate（status/deleted_at→8888），與 login 側互補、不重複驗密碼。★login 鎖內重驗中止路徑的 `sys_login_attempt` 稽核語意（島 E3 恰一列/節流計數）實作期明定。
- **Rationale**：審查 B1 blocker（跨併發鎖序/session撤銷/資料完整 3 鏡頭指認）：login 的密碼驗證＋活性讀在 advisory lock **之前**於外層 autocommit 連線跑，且無條件 insert active token；011 撤 session 用列鎖——正交鎖命名空間、互不阻擋。攻擊序：login 讀到活性→011 停用/刪除/改密 commit（revoke_all 掃不到未 commit 的新 token）→login commit 插入 active session＝**撤銷漏網**。改密尤毒：新 session 用舊密碼登入、refresh gate 只查 status/deleted_at（改密不動這兩者）→**可無限續命、改密除權完全失效**。統一 advisory lock 序列化 login 與撤 session 後：011 先 commit→login 鎖內見 status=2/deleted/新 hash→中止；login 先 commit→revoke_all 見新 token→撤掉。密碼 hash 字串比對成本極低（authenticate 已讀一次 hash、鎖內重讀比對），無需重跑 argon2。
- **Alternatives**：加 per-request user 活性 gate（enforce_mw 每請求查 sys_user status/deleted_at）——能根治停用/刪除，但對改密無效（status 不變）、且每請求多一次 DB 查、推翻 006「user 活性只在 login/refresh gate 查」分層。D13 user 親決不加、接受 denylist 失敗時 ≤access_secs 殘留窗（sensitive 面靠鎖序修法根治並發窗）。駁回加 gate。

## R4（B2）op-log payload 密碼白名單＋回應 DTO 逐欄構造（島 I5）

- **Decision**：sys_user 的 op-log payload **白名單欄位**（絕不含 password/session_id）；resetUserPassword 的 op-log payload 僅記 `{id, userName}` 類中性欄；deleteUser 的 payload 可含角色指派快照但排除 password。getUserList/getDeletedUsers 回應**逐欄構造**（比照 009 `role.rs get_role_list`、不序列化 raw sys_user Model）——絕不含 password（argon2 PHC）與 session_id。承載密碼的 DTO（AddUserReq/ResetUserPasswordReq）**不 derive Debug、手寫 impl Debug** 印 password 為 `<redacted>`。
- **Rationale**：審查 B2 blocker（密碼秘密/資料完整）：sys_user 若沿 sys_role 逐欄 AuditSerialize 範式倒出會把 argon2 hash 寫進 append-only 稽核（resetUserPassword before/after 各一枚 hash），永久留存＋DBA/備份/未來 op-log viewer 皆可讀＝離線爆破料。getUserList 授 R_ADMIN 可讀（唯一跨含密碼欄表的讀端）——直接序列化 Model 會批量洩 hash＋session_id。LoginReq 前例＝裸 derive Debug 含明文 password，fix 迴圈易誤加 `{:?}` 洩明文入容器 log。
- **Alternatives**：靠「沒人 print」的紀律——無機器防線、fix 迴圈易破，駁回。

## R5 密碼政策 enforcement 單一驗證點＋chars/bytes 雙約束（島 I5）

- **Decision**：`password.rs` 新增 `hash(password)→PHC`（argon2id、`Argon2::default()` 同 seed/verify 參數）＋`validate_against_policy(policy, user_name, candidate)→Result<(),Vec<違規碼>>`。單一驗證點、addUser＋resetUserPassword 共用。消費 7 鍵：`min/max_length`＝**chars 計**、另加固定上界 `candidate.len()(bytes) ≤ LOGIN_PASSWORD_MAX_BYTES`(512、引 007 常數不硬編)；`require_digit/lowercase/uppercase/special`＝字元類存在；`forbid_username`＝**case-insensitive 相等**（密碼 lowercase == 帳號 lowercase 即拒）。7 鍵**單快照讀**（find_by_keys 單語句、沿 007 throttle 前例）。★hash 於**取列鎖前**算（不夾鎖內）。
- **Rationale**：004 政策 7 鍵已 seed、現況零業務消費者——本刀首個真消費者。審查 serious 群：①長度單位未定＋未對齊 007 的 512 bytes→多位元組密碼「設得進登不進」（chars 政策＋bytes 上界解）；②forbid_username 三重未定（大小寫繞/子串 vs 相等矛盾/短帳號退化）——case-insensitive 相等對齊 m002 seed description「禁止密碼與帳號相同」、無短帳號退化；③torn read（逐鍵讀跨快照弱化）——單快照解；④argon2 夾鎖內拉長持有期（minor）——取鎖前算解。密碼 hash 生產入口現制不存在（僅 verify＋seed 期 hash），本刀新增。
- **Alternatives**：子串語意 forbid_username——與 seed description 矛盾、短帳號退化，駁回。前端 REG_PWD 為權威——前端硬正則 `^\w{6,18}$` 擋死政策合法密碼（特殊符號/長密碼），駁回（見 R8）。

## R6 刪除同交易硬刪指派列＋復原不回灌（島 I4）

- **Decision**：deleteUser 軟刪（deleted_at/by 成對）同交易**硬刪** sys_user_role 指派列；restoreUser 復原後**零角色**（須 super 重指派）、status 保留刪除前原值。restoreUser 鎖已刪列→鎖內重驗同名活性衝突（`userNameExists`、partial-uniq 索引 23505 兜底）。
- **Rationale**：009 deleteRole in-use 守門 `userCount`＝指派列總數、不濾 user status——軟刪 user 若保留指派列＝**幽靈掛載**，角色永不可刪、拒因人數失真。硬刪指派使 009 守門與計數誠實；復原不回灌＝與 009/010 零繼承/零回灌哲學一致（D11 user 親決）。sys_user_role FK ON DELETE RESTRICT 不擋軟刪（軟刪不動 user PK 列）、硬刪指派列亦不撞 FK（刪的是 join 列本身）。指派快照進 op-log payload_before 即史（排除 password、R4）。partial-uniq 索引（`sys_user_user_name_active_uniq WHERE deleted_at IS NULL`）為 restore 同名衝突守門的**顯式前提**（審查 minor：restore 鎖已刪列、addUser 插新列、二者不互鎖、正確性全靠此索引；測試須斷言索引存在）。
- **Alternatives**：保留指派列——幽靈掛載、與零回灌哲學相悖、需另設 userCount 濾軟刪（動 009 既有口徑＝跨刀行為變更），駁回。

## R7 batchDeleteUser＝fail-fast（沿 009 範式）

- **Decision**：batchDeleteUser 自管 txn、ids 去重升序、逐 id 同守門、**fail-fast**（首個違規即整批 rollback＋回該違規結構化拒因、不 collect-all）；已刪 id＝鎖列回 None→`userNotFound`→**整批拒**（違規、非冪等跳過）。
- **Rationale**：審查 serious 指設計「整批 rollback＋blocked 明細」自相矛盾（fail-fast 遇首違規即停、無法出完整明細；出完整明細須先驗完全部再 rollback）。沿 009 `batch_soft_delete` 既有 fail-fast 範式（首錯 return 該 Err、整批 rollback）＝跨刀一致。已刪 id 語意＝違規（鎖列濾 deleted_at IS NULL 回 None→NotFound），非冪等 skip——與 009 一致、且與同刀「23505→userNameExists 明確拒」風格一致。
- **Alternatives**：collect-all 全驗＋blocked 明細——與 009 fail-fast 不一致、複雜度高，駁回。冪等 skip 已刪 id——「刪了 3 個實際只動 2 個」誤導操作者，駁回。

## R8 登入頁前端規則放寬 required-only（審查 serious）

- **Decision**：`pwd-login.vue` 的 `REG_PWD`（`^\w{6,18}$`）／`REG_USER_NAME`（`^[一-龥a-zA-Z0-9_-]{4,16}$`）降為 required-only（後端政策為唯一權威守門）；走 fork-delta 修改型帶原行（登入頁 007 已是修改型檔）。addUser user_name 形制＝`^[A-Za-z0-9_-]{1,64}$`（非空、≤登入上限 64、零正規化＝島 E2）。★**§III.2 授權（analyze 補全）**：`pwd-login.vue` 在 `views/_builtin/login/`、非 `views/manage/**`——落在所有既有軌道射程外（MODAL-WIRING 限 manage／AUTH-WIRING 明文「不改 pwd-login」／LOGIN-CAPTCHA-WIRING 限 captcha 渲染）；此放寬 MUST 隨島 I MINOR Amendment **立新登入用途**（或擴既有登入軌道）、T029 於前端執行單元前 user 親決。
- **Rationale**：審查 serious：政策開 require_special 後，addUser 建的含特殊符號密碼（如 `NewOps-2026!`）在登入頁被 REG_PWD 前端擋死（`!` 非 `\w`、且政策長度可達 64 遠超 18）→帳號永遠登不進；REG_USER_NAME 4-16 也擋 addUser 的 3 字或 17+ 字帳號。「REG_PWD 不動」把矛盾凍進系統。後端才是唯一權威守門（登入端 throttle 形制上限＋密碼 verify）。
- **Alternatives**：addUser 收緊到 4-16 對齊登入頁——把 soybean demo 遺留的前端硬正則當設計約束，駁回；放寬前端＝正解。

## R9 前端接線軌道對號＋§III.2 Amendment（Q2/Q7）

- **Decision**：接真 API（index delete/batchDelete、drawer submit）＝MODAL-WIRING (a)；hasAuth gating＝(b)；onError 明細＋backend.biz 三語＝I18N-WIRING (i)(ii)(iii)。★超既有授權者（**四處**、analyze 補全）隨島 I MINOR Amendment 擴 §III.2：①回收桶「顯示已刪除」toggle＋逐列 restore＝擴 (d) 至 user 頁（(d) 現文「嚴格限選單樹」）；②頁首解鎖 modal（net-new）＋operate 欄 kick/reset-pwd 維運動作＝立新維運用途；③drawer 新表單控件（add 密碼欄＋004 政策 hint、edit session_policy select）＝超 (a)「placeholder 接線＋附屬小修」字面（upstream drawer 無此二控件）、須明確分類；④★pwd-login 放寬（`_builtin/login/`、既有軌道外、立新登入用途、見 R8）。fetcher＝WRAPPER `rev4-user-admin.ts`（**9 fetcher**、getUserList 複用凍結 fetchGetUserList、直接 import request 不經 barrel）＋ADAPT `rev4-user-admin.d.ts`（declaration merging、session_policy 併入 User）。
- **Rationale**：§III.2 七用途逐一比對：(a) 限既有 placeholder（user 頁模板有 edit/delete placeholder、無 kick/reset）；(c) 限「角色×權限維度」（解鎖非此）；(d) 明文「嚴格限選單樹復原/父層級調整」（射程不含 user 頁回收桶）。故回收桶 toggle、解鎖 modal、kick/reset 動作皆超界→須 Amendment（審查 serious「§III.2 Amendment 漏排」）。session_policy 併入 User 型為必要（審查 serious：drawer select 無來源讀現值→diff 誤判→靜默弱化他人 session_policy）。
- **Alternatives**：硬塞既有用途——(d) 文字「選單樹」明擋、(a) 無 kick/reset placeholder，牽強且違紀律，駁回。

## R10 撤 session 原語＋reason 映射（島 I2、島 C1）

- **Decision**：新原語 `sys_token::revoke_all_of_user(conn, uid)`＝`revoke_others_of_user` 薄變體（同 loop-until-0-active SELECT-driven 迴圈、不留 keep_sid、回 distinct sid）。reason 映射（006 FR-011 凍結）：停用/刪除/批刪/改密→session_event `revoked`＋denylist revoked（8888 靜默）；kickUser→`kicked`＋kicked（7777 阻斷 modal）。動作序（島 C1 PG-first）：txn｛業務寫＋token 轉 revoked＋session_event 逐 sid＋op-log｝→commit→best-effort denylist 逐 sid **TTL＝refresh_secs**。resetUserPassword 標的=operator 時 keep 當前 sid。
- **Rationale**：006 撤銷 primitive 齊備但缺「撤某 uid 全部 active」（現有 revoke_others 需 keep_sid）——薄變體填缺。session_event `revoked` 類保留至今零發出點＝本刀首用。TTL＝refresh_secs（非 access_secs）＝血淚教訓（auth.rs:311-314）：TTL 用 access_secs 會使被撤者持 refresh 換發時 denylist 已過期→假 reuse 稽核污染。run_refresh revoked 靜默分支（R3）消滅「revoked 換發誤標 reuse＋denylist TTL 縮短」minor。
- **Alternatives**：傳不存在 sid 借用 revoke_others——語意隱晦，薄變體更清晰，駁回。

## R11 session_policy UI＝獨立端點（島 A2）

- **Decision**：updateUserSessionPolicy 獨立端點（照 seed 意圖、super-only protected=true 已埋）；drawer edit 模式 session_policy select、diff 觸發獨立請求；後端值域驗（inherit/single/multi）＋no-op 判。改 single 不即時踢（下次登入 006 收斂、島 A2 解析階層無涉即時性）。getUserList 回應併入 session_policy 欄（讀取通道、R9）。
- **Rationale**：006 FR-004 遞延、端點 casbin 政策已預埋（protected=true）。獨立端點而非併入 updateUser——protected 授權語意獨立、改策略不需連帶其他欄。改 single 即時性＝下次登入收斂（brainstorm D7、與 006 single-session 機制一致）。
- **Alternatives**：併入 updateUser——protected 語意與一般欄混淆，駁回。

---

## 研究小結：3 blocker × 12 serious × 9 minor 折入落點

| 審查項 | 落點 |
|---|---|
| B1 並發登入漏撤（改密無限續命） | R2 統一 advisory 鎖序＋R3 login/refresh 鎖內重驗 |
| B2 op-log 洩 password PHC | R4 payload 白名單＋回應逐欄＋DTO Debug 遮蔽 |
| B3 seed 違反 ADR 0032 | R1 m008 顯式 migration |
| serious：ABBA 死鎖／login 造漏網 chain | R2/R3（併入 B1） |
| serious：停用路無兜底／denylist 寫失敗窗 | R10＋plan Constraints（≤access_secs 明文接受、D13） |
| serious：batch 語意矛盾 | R7 fail-fast |
| serious：登入頁正則不相容 | R8 放寬 required-only |
| serious：forbid_username／密碼長度單位／DTO Debug | R5＋R4 |
| serious：session_policy 讀通道 | R11＋R9（併入 User 型） |
| serious：§III.2 Amendment 漏排 | R9 |
| minor：partial-uniq 前提／code→id 整批拒／torn-read／reset 引導／argon2 鎖內／空字串守門 | R6／R7（code→id）／R5／plan（toast）／R5／data-model（沿 009 L-089/090） |

全 25 findings 有明確落點；無駁回項。zero 新錯誤碼、zero schema 變更（m008 純 seed）；casbin 6 端點已 seed、4 端點＋4 按鈕碼 m008 additive。
