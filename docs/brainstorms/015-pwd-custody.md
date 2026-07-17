# 015-pwd-custody 階段 0 brainstorm — 隨機產密＋密碼經手表＋首登強制換密（B-030 兌現）

- 日期：2026-07-17
- 方法：四鏡頭並行偵察（治理／rust-api 後端／base-web 前端／rev3 承襲）＋彙整 critic 交叉裁決
  （wf_ddcc0b57）→ 拍板題逐題親決（8 題、含 user 中途兩次規則升級：UI 動線重設計＋經手表模型）
  → 設計分節核可 → 3 鏡頭對抗式審查 → ADR 0067 draft 隨本檔同 commit。
- 存在理由：**B-030**（新帳號初始密碼政策化殘餘：隨機生成＋首登強制改密）——ADR 0055 拆階段
  預告、014 自助改密落地＝觸發條件達成（0055:35-37 殘餘義務逐字兌現）。
- 承襲基底：**rev3 純綠地**（K2-14／F-7 全程停在「登記候選」、rev3 未實作——sys_user 16 欄無旗標、
  login 無插閘、grep 全零命中；B-030 條目「加欄＋插閘＋改密頁」係 rev4 預估、本 brainstorm 已
  推翻其中「sys_user 加欄」半件）。後端底座＝rev4 014 as-built（changePassword 全鏈複用）。
- 下一步：本檔＋ADR 0067 draft → commit 落 default（rev4-admin-root）→ user 審 → 手動起手
  `/speckit-specify`（feature branch `015-pwd-custody` 由 specify 建）。

---

## §0 接地盤點（四鏡頭＋補充偵察實證精華）

### 0.1 治理面
- **ADR 0055 殘餘義務逐字**（0055:35-40）：隨機生成＋首登強制改密整包、觸發條件綁自助改密落地
  後；不變式＝密碼驗證 MUST 複用 ADR 0054 單一驗證點（禁止分叉）＋強制改密流程 MUST 沿島 I2
  撤 session 連動語意（改密撤他 session、保留當前操作 session）。
- **憲法 §I.6 變體 C 先例**（constitution.md:84）：sys_user_role＝零審計欄硬刪複合 PK；sys_token＝
  狀態機（憲法字面「僅 created_at＋status」；實表另有 created_by domain 欄——本表引法照
  archetype-map 轉述、非憲法逐字）——「無稽核欄、不軟刪」的新表落既有變體 C、**免修憲**
  （「用後即刪」精確語意＝僅他人設列被本人改密清除、自改列長存為錨）；建表手續＝data-model §1
  歸屬＋archetype-map.json 登記＋schema-gate STRUCT_ADDITIVE_ALLOWLIST（ADR 0039 表級白名單）＋
  **audit_table 變體 C 加 sys_pwd_custody 專屬分支＋TestAuditTable 案例同步**（audit 對變體 C 為
  表名硬編碼分支、schema-gate:585/589——不擴必紅）＋Compliance Q8。
- **十用途 (a)~(j) 無一涵蓋**強制改密頁＋route guard 攔截控制流（(g) 嚴格限 user-center 本人自助、
  AUTH-WIRING 限三處且不改 pwd-login、constitution.md:180 新用途自 (k) 起走 Amendment）→ 本刀
  需 MINOR Amendment。
- **島 I5 硬約束**（constitution.md:138）：API 回應 MUST NOT 含密碼——「後端生成隨機密碼回傳」
  正面衝突（D1 落選丙案的治理依據）。
- **schema-gate 白名單三條件**（schema-gate:258-263）：既有表加欄強制「型別對＋可空＋無預設」——
  sys_user 加 NOT NULL DEFAULT false 旗標欄必紅（經手表模型取代加欄後此約束不再觸及、僅記錄
  為 D3 落選案的機器依據）。

### 0.2 rust-api 面（014/011 底座）
- **login 全鏈**（handler/auth.rs:217-358）：形制閘→節流 precheck→authenticate（dummy_verify 拉平
  ＋record_attempt）→txn＋per-user advisory lock→鎖內重驗三前提→簽 token→insert sys_token→單一
  會話政策→成功稽核→commit。首登判定點在成功登入之後＝與島 E 判定序零互動。
- **changePassword 全鏈**（facade/sys_user.rs:1312-1396、data-model §4 固定序不得重排）：鎖外五拒因
  （notFound→confirm mismatch→舊密 verify→新≠舊→政策明細）→鎖內 phc 重驗→UPDATE→revoke_others
  keep=operator_sid→session_event(revoked)→op-log 白名單→commit。首登場景全數適用（「新≠舊」天然
  滿足「不得沿用經手密碼」）。
- **reset_password**（facade/sys_user.rs:1020-1089）：同骨架無舊密步、標的非本人 revoke_all、標的
  本人 keep-sid。**UpdateUserReq 無 password 欄**（改既有密碼唯一入口＝ResetUserPasswordReq
  {id, password}）；addUser（insert、豁免 advisory lock）＝011 已落政策驗證。
- **getUserInfo**（auth.rs:787-807）：本就重讀 sys_user 整列——加 EXISTS 判定僅 +1 主鍵查詢；
  in-crate 測試無欄位總數斷言（additive 安全、但新欄須配正負向新斷言防恆綠）。
- migration 慣例：mNNN 檔名、ADR 0032 run-once、本刀＝m011；settings seed 先例 m003/m005/m006。

### 0.3 base-web 面（011/014 as-built）
- **修改抽屜無密碼欄**（user-operate-drawer.vue:79 註解「欄僅 add 模式渲染」）——user 原述「修改
  抽屜加鈕」前提不成立、經 Q&A 改為 operate 欄「密碼」動作（前提糾正記錄）。
- **reset-pwd 現行形**＝operate 欄 dropdown 輕量 dialog（index.vue:293-322、收新密碼→
  resetUserPassword→resetPwdSuccess＋unlock 指引 toast）。
- **登入後路徑**：pwd-login handleSubmit→authStore.login→loginByToken→getUserInfo→redirectFromLogin；
  session 還原走 initUserInfo（route store:181-183）**不經 login action**——閘必須放 route guard
  全域層（僅 login action 分支＝可繞、已證僞）。
- **guard 主體**（router/guard/route.ts:35-52）＋auth store 均屬基線既有檔＝修改型 inline 帶
  `原行:`；`typings/api/auth.d.ts` 憲法凍結（constitution.md:238）→ needChangePwd typing 走
  net-new ADAPT declaration merging（同目錄 9 支 rev4-*.d.ts 先例）。
- **constant route 免曝光鏈**（store/modules/route/index.ts:163-164 靜態併集）：強制改密頁比照
  login/403（blank layout、hideInMenu）→ 後端路由面零改動。
- password-card 可搬用件：buildPolicyRules（7 鍵→naive rules 含 forbid_username 大小寫不敏感）、
  新≠舊即時 rule、confirm rule toRef 防快照、政策讀取靜默降級；★userName 必走 getProfile 真帳號
  （authStore.userInfo.userName＝nick_name 別名、憲法 L45 投影坑、014 U9 實證）。
- B-103 實測：email/phone 雙卡各 85 行、載碼差異恰四組字面——本刀零改動需求。

### 0.4 rev3 承襲鏡頭
- K2-14 出處鏈：rev3 CHECKLIST §4.2（INTEGRATION-CHECKLIST.md:201、初始密碼寫死 "123456" 不經
  政策）＋REVIEW-20260702 F-7＋rev4 bootstrap K2-14 條目——全程候選、無 as-built 可抄。
- rev3 K2-13 建議「改密後撤 session 在 auth 設計期直接內建」——rev4 014 已兌現、本刀沿用。

## §1 拍板（user 親決 8 題、2026-07-17；D 序＝定案順序）

- **D1 隨機生成入刀＝前端本地生成＋產密浮層**：瀏覽器本地生成合政策密碼、伺服器回應不含密碼
  （零島 I5 衝突、後端零生成邏輯）。浮層規格（user 直述）：「產生」＋唯讀 input＋「顯示密碼」
  切換＋「複製」＋「帶入」。落選：本刀不做再拆條目（B-030 無法一刀收）；後端生成一次性回傳
  （正面撞島 I5、須修憲釋義、不默做）。
- **D2 manage 端「密碼」鈕與既有「重設密碼」並存**：operate 欄新「密碼」動作＝隨機專用浮層
  （input 唯讀、只能產生填入、浮層內確認送出）；「重設密碼」手輸 dialog UI 零改動。落選：合一
  取代（動 011 既有 UI、(h) 字面改寫面大）。前提糾正記錄：user 原述「修改抽屜密碼欄加鈕」——
  實測修改抽屜無密碼欄（0.3）、經確認改落 operate 欄。
- **D3 經手表模型 `sys_pwd_custody`（user 提出、取代 sys_user 加欄）**：每次設密寫「誰幫誰設」
  ——`user_id`＋`created_by`（複合主鍵；零 FK、見 §2.1）＋`created_at`（NN default now()）。
  **判定**（login／getUserInfo／API 硬閘共用單一規則）：該 user 名下存在任一筆
  `user_id≠created_by` → 首登須換密；純自改列或零列 → 不強制。**寫入**：別人設→upsert
  `(user, admin)` 刷新 created_at；本人改→同交易**全刪＋寫一筆 `(user, user)`**（全刪範圍恆＝
  `WHERE user_id=標的`名下列、絕非 created_by；自改列長存＝最後本人改密時間、為未來密碼有效期
  留錨）。變體 C、不軟刪、不存密碼。落選：sys_user 加
  nullable 旗標欄（單欄無法承載「誰經手」語意）；NOT NULL DEFAULT false 欄（schema-gate 三條件
  必紅、需工具級 ADR）。
- **D4 一體適用規則**：凡 admin 經手設定的密碼（**建帳 addUser＋重設手輸＋「密碼」鈕隨機**）
  一律入列→本人首登必換；Super／Admin／User 三 seed 帳號 migration 直寫無操作者→零列不補
  （demo 零阻礙）；admin 對 seed 帳號日後重設→同樣強制（規則一體適用的正常結果、憲法 I3
  「Super MAY 被重設密碼」相容）。admin 對**自己**重設＝operator=標的→走「本人改」路徑（全刪
  ＋寫自列、不強制）——規則單一（operator=標的即本人改）；實作沿 reset_password 既有 keep-sid
  自我分支點（sys_user.rs:1069-1073）同點分岔、custody 寫入語意以本條為準（§2.2 同義；對抗式
  審查 BK1 收斂）。
- **D5 插閘＝A＋硬閘（鎖態 token）**：登入照常發 token；getUserInfo 曝 `needChangePwd`；前端
  route guard 全域閘攔至強制改密專頁；後端 middleware 硬閘——判定為真時白名單外一律 2222
  `mustChangePassword`（含 curl 直打）。落選：C 不發 token＋login 頁內改（需新開 Public 改密
  端點＝第二個未認證驗密 oracle、須整套接 007 節流＋稽核終局新語意＋政策端點公開化＋撞
  AUTH-WIRING(b) 不改 pwd-login——用更大攻擊面保護已持真密碼者、不值）；純前端閘（user 明確
  要求 API 面也擋）；claims 烙旗標（違 claims hint-only 紀律＋keep-sid 殘留、兩鏡頭一致排除）。
- **D6 改完立即登出重登**：強制頁改密成功→前端呼 logout→回登入頁→持新密碼重登。後端
  changePassword 語意**零偏差**（keep-sid＋撤他裝置照 014）→ **ADR 0055 不變式字面維持成立**
  （登出由既有 logout 端點達成、非後端撤本 sid）。
- **D7 設密冷卻（user 提出）**：同一 `(user_id, created_by)` 對距上次 `created_at` 未滿 N 秒
  再次設密→拒（2222＋新鍵）；N＝system_settings 新鍵（`/manage/system-settings` 可調）、m011
  seed。劃界：只限制**成功改密**頻率、失敗嘗試不寫列不受冷卻——**非 B-102**（舊密暴力試節流、
  照 roadmap 留 auth 延伸組）。冷卻按 pair 計＝不同 admin 對同一標的連續重設互不受限（字面既定、
  備查）。已識別自鎖窗：user 自改後 N 秒內被 admin 重設→強制頁自改撞自列冷卻、最長鎖出 N 秒
  （預設 60 自癒）——specify 期擇一：強制態（存在非自列）自改豁免冷卻（傾向）或拒絕 UX 顯示
  剩餘秒數。
- **D8 B-103 順路評裁定＝不提煉＋釐清條目措辭**：本刀僅碰改密卡（加隨機鈕）、雙卡零改動；
  提煉＝scope 蔓延（012 B-096 同構容忍先例在場）。收刀時 BACKLOG 條目觸發措辭改「觸及
  email/phone 雙卡本體時」。

## §2 設計總表（分節核可版、user 核可 2026-07-17）

### §2.1 資料模型
- 新表 `sys_pwd_custody`：`user_id bigint`＋`created_by bigint`（複合 PK；**零 FK**——沿 ADR
  0009「其餘業務表零 FK、參照完整性應用層承擔」既定原則對齊〔ADR 0067 明文引用、審查 BK5〕，
  並消除雙 FK 對 sys_user 交叉列鎖的併發死鎖窗）＋`created_at timestamptz NOT NULL DEFAULT
  now()`（語意＝該對最後設定時間、archetype-map note 正名）。變體 C、硬刪、不存密碼。
- migration **m011**：建表＋system_settings 新鍵 seed（`password_change_min_interval`、預設 60、
  0＝不限制）。工具聯動（同 commit、缺一即紅）：schema-gate STRUCT_ADDITIVE_ALLOWLIST（表級）＋
  SEED_ADDITIVE_ALLOWLIST（settings 鍵）＋**audit_table 變體 C 加 sys_pwd_custody 專屬分支**
  （現行表名硬編碼、schema-gate:585/589、審查 BK4）＋TestAuditTable 案例與 self-test dict 同步＋
  archetype-map.json 登記（note 記 created_at 語意）＋data-model §1 歸屬補列。
- 無 backfill：015 前既有帳號與 seed 三帳號零列＝不強制（明文劃界；custody 表出現前的自改史
  無從辨識、不回填為合理預設）。

### §2.2 後端（零新端點、零新錯誤碼；回應 DTO 僅 getUserInfo additive 加欄〔審查 BK2 措辭修正〕）
- facade 三寫入：`insert`（addUser）append `(new, admin)`；`reset_password`——operator≠標的→
  upsert `(target, admin)`＋冷卻檢查、operator=標的→本人改路徑（全刪＋寫自列；沿既有 keep-sid
  自我分支點 sys_user.rs:1069-1073 同點分岔、審查 BK1 收斂）；`change_own_password` 全刪＋寫
  `(self, self)`＋冷卻檢查（對自列）。「全刪」範圍恆＝`WHERE user_id=標的`。全在既有交易＋
  advisory 鎖內原子完成（addUser 沿既有豁免鎖——新列 commit 前不可見、custody 列同批 insert）。
- 冷卻檢查位置：鎖內、**各端點既有拒因全過之後**、UPDATE 之前（change_own_password 五拒因、
  reset_password 二拒因；序零重排；沿「新≠舊」端點固有規則分層判例、不入 ADR 0054 單一驗證
  點）；設定單鍵讀、缺鍵 fail-default 60。
- `get_user_info` 加 `needChangePwd`（EXISTS 主鍵查詢；additive、前端宣告 optional）＋正負向
  新斷言。
- API 硬閘 middleware（enforce_mw 之後、**authed 與 policy 兩子 router 皆掛**——漏掛 policy＝
  有管理權的被強制者可打全部 manage 端點）：判定真→白名單外 2222 `mustChangePassword`。白名單
  （path 字面匹配、GATE_BYPASS_ENDPOINTS 先例 middleware/mod.rs:115）＝changePassword／
  getPasswordPolicy／getUserInfo／getUserRoutes／getProfile（強制頁取真帳號名）／isRouteExist
  （guard 路由存在性解析、強制態深連結不炸）；白名單僅約束 Authed/Policy 路由——logout 與
  refreshToken 本為 Public 子 router、結構上不經閘（明載防誤讀）。middleware 疊放序凍結註記
  （router.rs:719-724）與 2222 拒是否入 access_log 之疊放位隨本刀治理處理。

### §2.3 前端
- 產密浮層元件（net-new 一支共用）；三掛載點：①add 抽屜密碼欄旁「隨機密碼」→帶入密碼欄
  ②operate 欄「密碼」→浮層內確認送出 resetUserPassword ③user-center 改密卡儲存前「隨機密碼」
  →帶入新密碼＋確認。鈕文案統一「隨機密碼」。
- 強制改密專頁：constant route（blank layout、hideInMenu、免後端曝光鏈）；表單＝舊密＋新密＋
  確認（＋隨機鈕）；政策 rules 與 password-card 共用（buildPolicyRules 抽 hook、net-new 檔內
  重排不動基線行）；成功→toast→logout→登入頁。
- route guard 全域閘（isLogin＋needChangePwd＋目的地非強制頁→改寫導向、判定置於路由存在性
  解析之先；直輸 URL／F5／深連結全覆蓋）。**不做 axios 攔截器兜底**（審查 BK3 裁定：憲法攔截器
  禁令字面〔constitution.md:204/224/236〕；「admin 重設活躍 session」情境已由既有 8888 撤銷管線
  覆蓋——reset 即 revoke_all、殘留分頁下一請求即登出，兜底價值稀薄不值破軌道）。guard／auth
  store＝修改型 inline 帶 `原行:`；typing 走 ADAPT declaration merging（不動凍結 auth.d.ts；對
  凍結 interface 之成員級擴充＝rev4 首例、spec 明載並驗 contract 測試吃合併後視圖）。

### §2.4 治理
- 憲法 MINOR Amendment：新用途 **(k)** 枚舉（審查 BK3 補全）＝強制改密頁（constant route）＋
  route guard 攔截控制流＋auth store inline＋manage「密碼」動作與浮層＋add 抽屜隨機鈕＋
  user-center 改密卡隨機鈕（(g) 射程確認句）＋**「＋對應 i18n key」字樣自始寫入**（v1.12.0 (g)
  補擴同判例、防重演）；順帶勘誤 constitution.md:195「九用途」與 :180「十用途」失步（v1.13.0
  遺留）。＋Compliance Q8（新表——答案含變體 C 歸類論證與 audit 分支聯動、非僅「落變體 C」
  一句）＋Q9 行為島判定（傾向＝島 I 新細項：經手判定規則／寫入規則／冷卻／硬閘白名單語意；
  並明文論證硬閘每請求 EXISTS 與島 I2「MUST NOT 每請求活性判定」的射程區隔——該禁令限撤銷
  即時性、custody 閘不在射程；specify/plan Constitution Check 定案）。
- ADR 0067 draft（隨本檔同 commit）：D3＋D5 選型本體；0054 複用、0055 不變式對齊明載。

### §2.5 i18n（三語＋App.I18n.Schema 鏡像）
浮層節（隨機密碼／產生／複製／顯示密碼／帶入）＋manage「密碼」動作鍵＋強制頁節（route 鍵＋
標題＋說明＋成功句）＋`backend.biz.user.pwdSetTooFrequent`＋`backend.biz.auth.mustChangePassword`
＋settings 標籤 `passwordChangeMinInterval`。

### §2.6 測試與驗收
- rust：判定三態（零列／純自列／混合）；三寫入路徑；冷卻正負向（未滿拒／已滿過／0 停用）；
  getUserInfo 欄正負向；硬閘白名單內外正負向；五拒因序既有測試零轉紅；contract registry 同步。
- CDP 實彈：①admin 隨機→member 首登被攔→token 直打列表 API 被 2222→改完自動登出→新密重登
  暢行 ②手輸重設同觸發 ③建帳首登觸發 ④seed 三帳號零影響 ⑤冷卻連按即拒 ⑥user-center 自助
  （含隨機）不觸發強制、014 行為不變 ⑦三語零 raw key。
- 全量閘：schema-gate 三子命令＋typecheck＋fork-delta-lint＋contract bijective。

### §2.7 收刀劃界
B-030 刪列；B-103 條目措辭改「觸及 email/phone 雙卡本體時」；B-102 條目不動；NOTES 下一步
指向 B-060。

## §3 工程自決報備（主線自拍、user 可否決）

1. settings 鍵名 `password_change_min_interval`（單位秒）、seed 預設 60、0＝不限制（上線可調、
   預設低風險）。
2. upsert 實作形：ON CONFLICT `(user_id, created_by)` DO UPDATE `created_at`（冷卻檢查前置於
   同鎖內）。
3. 白名單含 getProfile 的理由：強制頁前端政策提示需真帳號名（nick_name 別名坑、L45）。
4. 浮層生成演算法：MUST 用 CSPRNG（`crypto.getRandomValues`、勿 Math.random）、字元集構造性
   滿足政策 7 鍵（讀 getPasswordPolicy——admin 端 Authed 可用）；強制頁情境浮層強調「複製後
   送出」（產隨機未抄存即送出→登出後鎖出、需 admin 再重設）。
5. 強制頁 route 命名與佈局比照 login 系 constant route；頁上保留隨機鈕（同元件零成本、自改
   語意一致）。
6. 「送出值＝＝產生值」前端判定機制**整段不需要**（D4 一體適用後隨機/手輸同語意）——記錄
   以免 specify 期誤復活。
7. B-102 劃界句與 D7 冷卻的關係明載 spec（防誤判「已解」）。
8. 軟刪／復原與 custody 列互動：軟刪不清列（登入本被活性擋）、復原後判定沿刪前態（密碼未變、
   語意合理）——spec 一句明載。
9. auth store `needChangePwd` 宣告 optional（reactive 初始物件免補初值＝少一處基線修改）。

## §4 對抗式審查（3 鏡頭、wf_c3b4f487、2026-07-17）

- 結果：blocker 8 條（安全狀態機 3／治理合規 3／工程接地 2、跨鏡頭去重後 5 組）＋suggestion
  十餘條；全數處置、修訂已回灌本檔與 ADR 0067。攻擊未果項（主張經實碼驗證成立）：狀態機完備
  （全 repo 密碼寫入點四處全涵蓋、UpdateUserReq 無 password 欄零旁路）；並發（advisory 同鎖
  覆蓋雙方）；硬閘繞過面（白名單皆唯讀自身或解鎖必需；refresh/logout Public 結構性不經閘）；
  冷卻 DoS 不成立（pair 鍵第三方構造不出）；島 E2/E3 零互動；島 I5 零新增洩漏面；D6 對 0055
  不變式對齊論證成立；0054 冷卻分層判定成立；ADR 0067 front-matter 過 docs-sync L8。
- **BK1 custody 寫入語意三處矛盾** → 收斂：operator=標的即本人改（全刪＋寫自列）、沿
  reset_password 既有 keep-sid 自我分支點同點分岔；「免例外分支」措辭刪除。race 殘局兩讀法皆
  fail-safe（誤強制不誤放行）。
- **BK2「零 DTO 變更」自相矛盾** → §2.2 標題改「回應 DTO 僅 getUserInfo additive 加欄」。
- **BK3 axios 攔截兜底無軌道授權**（憲法 :204/224/236 三處禁令、(k) 枚舉未含）→ 刪除兜底
  （8888 撤銷管線已覆蓋活躍 session 情境）；guard 判定前置＋isRouteExist 入白名單；(k) 枚舉
  補全（auth store／兩處隨機鈕／「＋對應 i18n key」字樣）。
- **BK4 schema-gate audit 變體 C 表名硬編碼**（登記後必紅）→ 工具聯動補 audit_table 分支＋
  TestAuditTable 案例同步。
- **BK5 FK 撞 ADR 0009「其餘業務表零 FK」＋雙 FK 死鎖窗** → 拔 FK、零 FK 定案、ADR 0067
  明文引 0009 對齊。
- 採納 suggestion：冷卻位置措辭「各端點既有拒因全過之後」（reset 僅二拒因）；硬閘明定掛
  authed＋policy 兩子 router、path 字面匹配；Public 不經閘明載；冷卻 pair 計消歧義＋強制態
  自改豁免傾向（specify 拍）；CSPRNG 強制；「全刪」範圍精確化；存量零列劃界；軟刪／復原
  互動句；變體 C 引文正名；needChangePwd optional；憲法九／十用途失步勘誤排入 Amendment。
