---
id: "0053"
title: 使用者域狀態機總綱——統一序列化鎖序＋撤 session 連動＋seed 帳號結構保護＋B1 login/refresh 鎖內重驗（島 I 設計理據）
date: 2026-07-14
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-13 011-user-admin brainstorm D10~D13（user 逐題親決）＋6 鏡頭對抗式審查 25 findings 全折入（3 blocker：B1 並發登入漏撤／B2 op-log 洩 PHC／B3 seed 違 ADR 0032）＋plan Phase 0 research R2（統一序列化域）／R3（B1 鎖內重驗）／R6（硬刪指派＋復原不回灌）／R10（revoke_all 原語＋reason 映射）；憲法 v1.8.0 島 I 之設計理據檔（Amendment 本身＝T029 user 親決、條文草案見本檔附錄）"
tags: [user, state-machine, concurrency, session, authz, governance]
---

## 背景

011-user-admin 把基線預埋的使用者域端點（現況＝零、全新地）接成活的：10 端點（CRUD 五端點＋
kickUser／resetUserPassword／getDeletedUsers／restoreUser／updateUserSessionPolicy）＋角色指派寫端
（sys_user_role 第一個 production 寫入面）＋撤 session 連動，並兌現六刀遞延承諾（006 B-064 撤銷
primitive 消費端、009 島 G5／B-084 指派鎖序、B-029 改密撤 session、B-025 帳號名不可變後端半）。

使用者與角色／選單的關鍵差異＝**使用者列同時是登入身分的錨**：login/refresh 流程持續對 sys_user
併發讀寫（authenticate 讀 hash、insert token、write_session_id），而本刀的停用／刪除／改密寫端
要撤銷該身分的全部 session。對抗式審查（2026-07-13、6 鏡頭、25 findings 全折入零駁回）指認
blocker B1：login 的密碼驗證＋活性讀在 advisory lock **之前**於外層 autocommit 連線跑、且無條件
insert active token；若 011 撤銷寫端只用列鎖（與 login 的 advisory 鎖正交、互不阻擋），攻擊序
「login 讀到活性→011 停用/刪除/改密 commit（revoke_all 掃不到未 commit 的新 token）→login
commit 插入 active session」＝**撤銷漏網**。改密尤毒：新 session 以舊密碼登入，refresh gate 只查
status/deleted_at（改密不動此二欄）→漏網 session **可無限續命、改密除權完全失效**。另指認純列鎖
方案與 login 取鎖方向相反（login＝先 sys_token 後 sys_user；011 撤銷＝先 sys_user 後 sys_token）
＝ABBA 死鎖。

## 決定

使用者域為新行為島（島 I），五條不變式之設計理據如下（條文草案見附錄、T029 user 親決後入憲
＝v1.9.0 MINOR）：

- **I1 統一序列化＋固定鎖序（R2、D12）**：一切**以既有使用者為標的**的使用者域寫端（更新／刪除／
  批刪／重設密碼／踢除／復原／會話策略）於 txn 起手取 `pg_advisory_xact_lock(uid)`——**與
  login/refresh 共用同一把鎖**（auth.rs 既有）；域內固定鎖序＝①sys_user 標的列 `FOR UPDATE`
  （活性版 `find_active_by_id_for_update`；restore 用已刪列版 `find_deleted_by_id_for_update`）→
  ②sys_role 列（僅指派路、id 升序、複用 009 helper＝島 G5／B-084 兌現）→③sys_user_role 寫入，
  禁反向。advisory 首鎖統一了 login 與撤銷寫端的取鎖方向差→ABBA 死鎖消滅；與 009 鎖序
  （archive→sys_role→casbin/sys_user_role、不鎖 sys_user）無死鎖環。★addUser 豁免 advisory
  （新列無既有 uid、交易提交前對並發不可見、不涉 session 撤銷；並發同名保護＝partial-uniq
  23505）。一切守門鎖內重驗（lock-then-redecide、永不信 pre-read；與島 G5／B2／H1 同範式）。
  partial-uniq 索引 `sys_user_user_name_active_uniq` 為 restore 同名衝突守門的**顯式前提**
  （測試須斷言索引存在）。
- **I2 撤銷連動同交易＋PG-first＋B1 login/refresh 鎖內重驗（R3、R10、D13）**：停用（1→2）／刪除／
  批刪／改密 MUST 同交易消費新原語 `revoke_all_of_user`（`revoke_others_of_user` 薄變體、不留
  keep_sid、loop-until-0-active）＋session_event(`revoked`)＋denylist(revoked、8888 靜默)；kickUser
  →`kicked`＋7777 阻斷 modal；兩類體驗碼不可互換（006 凍結）。動作序＝島 C1 PG-first：txn｛業務寫
  ＋token 轉 revoked＋session_event＋op-log｝→commit→best-effort denylist 逐 sid、★TTL＝
  refresh_secs（用 access_secs 會重演假 reuse 稽核污染、auth.rs 血淚）。即時性上界明文＝denylist
  成功即時、失敗 ≤access_secs（refresh gate 兜底、沿島 C fail-open）；不加 per-request 活性判定
  （D13 親決、不推翻 006 分層）。★**B1 修法（動 005/006 既有碼）**：`run_login` 取 advisory lock
  後、insert token **前**，於 txn 內重讀 sys_user 列並重驗 `status==1 && deleted_at IS NULL &&
  password == authenticate 所讀 hash`（純字串比對、不重跑 argon2）——任一不符→中止回 1000、不
  insert token（堵「舊密碼 session 產生入口」與並發漏網 session、結構性不可達）；`run_refresh`
  為 `revoked` reason 增「合法撤銷、靜默 8888、不落 reuse 事件」分支（FR-020、不污染稽核），
  ★換發側**不重驗密碼雜湊**（login 側已堵入口、換發只延續已合法簽發之 chain；漏撤保障＝換發憑證
  列鎖鏈序列化＋活性 gate，與 login 側互補不重複）。
- **I3 seed 帳號結構保護（D10）**：三 seed 帳號（id∈{1,2,3}、hardcode 對稱角色側
  `SEEDED_ROLE_IDS`）不可刪；Super（id=1）額外不可停用、不可解除其 R_SUPER 指派——五道護欄閉合
  （deleteUser/batch seeded 守門／updateUser 停用路 `superCannotDisable`／指派路
  `superRoleProtected`／R_SUPER 角色本身受 009 雙護／reset·kick·restore·sessionPolicy 均不動 id=1
  之刪除態/status/指派）→系統恆有 ≥1 活躍且啟用之超管，**結構保證、不需動態計數**。Super 可被踢
  （無永久傷害、可重登）、可重設密碼。self 守門＝操作者不可刪除／停用／踢除自己、不可改自己的
  角色指派（防自鎖／自廢 R_SUPER，與 I3 互補涵蓋「經自身帳號清空超管」兩路徑）。
- **I4 刪除清指派＋復原不回灌（R6、D11）**：deleteUser 軟刪（deleted_at/by 成對）MUST 同交易
  **硬刪** sys_user_role 全指派列（零幽靈掛載→009 deleteRole 掛載計數守門誠實）；restoreUser
  復原後**零角色**（須 super 重指派）、status 保留刪除前原值（誠實）。同帳號名重建零繼承＝雙封
  （硬刪指派＋復原不回灌；新使用者識別不同、指派以識別為鍵）。批刪＝自管單一 txn、ids 去重升序、
  fail-fast 整批拒（含已刪 id＝違規非冪等跳過；沿 009 範式、R7）。
- **I5 密碼政策單一驗證點＋密碼三重不洩**：設計理據獨立成篇＝ADR 0054（本島條文涵蓋、細節見彼）。

## 後果

- **零 schema 變更（零建表零加欄零改欄）、零新錯誤碼**；唯一資料面新增＝m008 seed-only migration
  （casbin_rule 8 列 additive、SEED_ADDITIVE_ALLOWLIST 同步登記＝審查 B3 修正、ADR 0032）。
- **B1 動既有 auth 碼**（run_login/run_refresh）：地基階段優先落定＋負向自證（拆鎖內重驗→併發測試
  轉紅）＋併發機器證第 4 組 load-bearing＋既有 005/006 測試零轉紅盤點。
- login 鎖內重驗中止路徑的 sys_login_attempt 稽核語意（島 E3 恰一列／節流計數）實作期明定並在
  測試斷言（罕見競態終局：該次已過密碼驗證但因活性/密碼變動中止）。
- 方向性面凍結（入憲後反轉＝MAJOR）：拆散統一序列化（advisory 與 login 脫鉤）、拔 login 鎖內重驗、
  改 PG-first 為廣播優先、開放 seed 帳號守門、改整批拒為部分成功、復原回灌指派——皆 MAJOR；
  常數（advisory key＝uid、TTL 來源、SEEDED ids 字面）留活書。
- 審查缺陷群溯源：B1→I1+I2；ABBA 死鎖→I1；停用路兜底／denylist 寫失敗窗→I2 明文上界；batch
  語意矛盾→I4 fail-fast；B2 op-log 洩 PHC→I5（ADR 0054）；B3 seed→m008（ADR 0032 既有紀律）。

## 附錄：憲法 Amendment 草案全文（T029 user 親決時貼入 constitution.md；★本檔不動憲法本體）

### A. §I.7 新增島 I 條文草案（v1.9.0、MINOR）

> - **島 I — 使用者域治理**（011、ADR 0053 總綱／0054 密碼政策）
>   - **I1 統一序列化與固定鎖序**：一切以既有使用者為標的之使用者域寫端（含撤 session 者：更新、刪除、批刪、重設密碼、踢除、復原、會話策略）MUST 於交易起手取得與登入／換發同源的每使用者序列化鎖（DB 交易級 advisory 鎖、key＝使用者識別、與 login/refresh 共鎖）；域內固定鎖序 MUST 為①標的使用者列 `FOR UPDATE`（復原用已刪列版）→②角色列（僅指派路、識別升序、複用角色域鎖讀）→③指派列寫入，禁反向；一切守門判定 MUST 鎖內重驗（lock-then-redecide、永不信 pre-read；與島 G5／B2／H1 同範式）。新增使用者豁免每使用者鎖（新識別對並發不可見；並發同名保護＝帳號名活性唯一約束）。帳號名活性 partial-uniq 索引為復原同名衝突守門之顯式前提。★方向反轉（拆散統一序列化、改回無鎖 pre-read）＝MAJOR。
>   - **I2 撤銷連動同交易＋權威優先＋登入鎖內重驗**：停用／刪除／改密 MUST 同交易撤銷標的使用者全部既有 session（撤銷類、靜默）；踢除＝踢除類（阻斷）；兩類體驗碼 MUST NOT 互換。動作序 MUST 權威優先（業務寫＋session 作廢＋稽核同交易落定→commit→失效廣播 best-effort、存活時間覆蓋換發憑證壽命）；即時性契約＝廣播成功即時、失敗殘留窗上界 access token 壽命（換發期活性守門兜底、沿島 C fail-open），MUST NOT 為此新增每請求活性判定。登入流程 MUST 於序列化鎖內、發 token 前重讀標的列並重驗活性與密碼雜湊（與驗證階段所讀一致、純比對不重跑雜湊），任一不符 MUST 中止不發 token；換發流程 MUST 於換發憑證列鎖內重驗使用者活性（不另重驗密碼雜湊）；被合法撤銷者換發 MUST 靜默拒絕、MUST NOT 誤判為憑證盜用。★方向反轉（拔登入鎖內重驗、改廣播優先）＝MAJOR。
>   - **I3 seed 帳號結構保護**：前三個種子帳號 MUST 不可刪；第一個（Super）MUST 恆禁停用、恆禁解除其超管角色指派（不因操作者身分而異）——系統恆有至少一個活躍且啟用的超級管理員（結構保證、不需動態計數）；Super MAY 被踢除、被重設密碼。操作者 MUST NOT 刪除／停用／踢除自己、MUST NOT 變更自己的角色指派。
>   - **I4 刪除清指派＋復原不回灌**：使用者軟刪 MUST 同交易硬刪其全部角色指派列（零幽靈掛載、角色域掛載計數守門保持誠實）；復原 MUST NOT 回灌任何指派（復原後零角色、須重新指派）、狀態保留刪除前原值；同帳號名重建之新使用者 MUST NOT 經任何路徑繼承舊實例角色。批次刪除逐項驗證、任一違規（含已刪識別）**整批拒**（fail-fast、單一交易、識別去重升序取鎖）。
>   - **I5 密碼政策單一驗證點＋密碼三重不洩**：密碼政策驗證 MUST 為單一驗證點（建帳與重設共用、零分叉）、政策鍵單一快照讀取；長度單位＝字元、另加固定位元組上界 ≤登入端形制上限；「禁止密碼與帳號名相同」＝大小寫不敏感相等。密碼明文與雜湊 MUST NOT 洩漏於任何面：承載密碼之 DTO 除錯輸出 MUST 遮蔽（不得預設印出）；操作稽核 payload MUST NOT 含密碼明文／雜湊／會話識別；API 回應 MUST NOT 含密碼與會話識別（列表逐欄構造、不序列化原始列）；密碼雜湊 MUST NOT 於持有列鎖期間計算。★方向反轉（拆單一驗證點、拔遮蔽）＝MAJOR。

### B. §III.2 軌道擴展草案（四處、隨島 I MINOR 同 bump；用途字串變更處逐字列出）

1. **MODAL-WIRING (d) 錨點與用途擴充**（(d) 條目改為）：

   > **(d)** 選單／使用者復原、re-parent 維運控制：`menu-operate-modal.vue` edit 模式 parentId selector＋`views/manage/menu/index.vue` 與 `views/manage/user/index.vue` 的「顯示已刪除」列表切換（toggle）＋逐列 restore 鈕＋對應 i18n key——嚴格限「選單樹復原／父層級調整／使用者回收桶復原」

2. **MODAL-WIRING 新用途 (h)——manage 頁維運動作**（新增條目）：

   > **(h)** manage 頁維運動作：`views/manage/user/index.vue` 頁首維運 modal 觸發鈕＋net-new `modules/user-unlock-modal.vue`（登入解鎖：dimension 選擇＋目標輸入→既有 unlockLogin 端點）＋operate 欄維運動作（kick／reset-pwd、NDropdown 收納）＋對應 i18n key——嚴格限「使用者頁既有後端維運端點之觸發 UI」、不擴張到新後端能力／任意新 UI
3. **MODAL-WIRING (a) 分類釐清——drawer 接線必要控件**（(a) 條目尾追加一句）：

   > create/update 接線所必要之表單控件屬本用途（如 user drawer add 模式密碼欄＋政策提示、edit 模式 session_policy 選擇器——payload 必要欄之輸入載體），仍限既有 operate-modal/drawer 檔內、不含新 modal
4. **新軌道用途——登入表單規則放寬**（LOGIN-CAPTCHA-WIRING 新增用途 (ii)，或依 user 親決立獨立軌道）：

   > **(ii)** 密碼登入表單前端規則放寬：`src/views/_builtin/login/modules/pwd-login.vue` 的 REG_PWD／REG_USER_NAME 表單規則降為 required-only（後端政策為唯一權威守門；消滅「政策合法密碼／帳號名被前端硬正則擋死＝設得進登不進」）——嚴格限「規則放寬」、不改表單結構／不改攔截器控制流／修改型帶 `原行:`

（提案理由：pwd-login.vue 在 `views/_builtin/login/`、落在 MODAL-WIRING〔限 manage〕／AUTH-WIRING
〔明文不改 pwd-login〕／LOGIN-CAPTCHA-WIRING〔限 captcha 渲染〕全部既有射程之外——analyze 補全
之第④處，MUST 經 Amendment 授權；T029 親決時可改掛他軌、以 user 拍板為準。）
