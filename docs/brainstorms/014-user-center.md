# 014-user-center 階段 0 brainstorm — 個人中心自助頁（B-090 兌現）

- 日期：2026-07-17
- 方法：五鏡頭並行深度探索（rev3 前端 UI／後端契約／治理設計依據／rev4 差異面／CDP 實機快照）＋彙整 critic 交叉裁決（wf_908112ab）→ 拍板題 4 題逐題親決＋工程級 9 項自拍報備 → 設計分節核可 → 3 鏡頭對抗式審查 → ADR 0065 draft 隨本檔同 commit。
- 存在理由：**B-090**（使用者自助改密；011 clarification user 親決＋ADR 0055 拆階段的前置兌現）——ADR 0055 明文 B-030（隨機生成＋首登強制改密）觸發條件綁「自助改密落地後」，本刀完成即解鎖 B-030。
- 承襲基底：**rev3 025-user-center 刀 as-built**（user 拍板 2026-07-17：全頁承襲、UI 全部要一樣——含 profile 編輯與驗證碼預留 UI；rev3 為受控參照不拷貝、§I.5）。
- 下一步：本檔＋ADR 0065 → `tools/docs-sync generate` → commit 落 default（rev4-admin-root）→ user 審 → 手動起手 `/speckit-specify`（feature branch `014-user-center` 由 specify 建）。

---

## §0 接地盤點（探索實證精華；rev3 引用相對其 repo）

### 0.1 rev3 成品形狀（承襲藍本）
- **頁**：`/user-center` 單欄縱排 4 卡（修改密码→邮箱→手机号→基本资料；`flex-col-stretch gap-16px`、rev3 index.vue:72）；每卡 NCard `bordered=false size=small segmented card-wrapper`、儲存鈕在 `#header-extra`（primary small）；卡內 NGrid `cols="1 s:2" responsive="screen" :x-gap="24"`（password 卡 label-width 100、其餘 76——刻意差異照抄勿統一）。
- **資料流**：index.vue 持 canonical ProfileModel 單一真相、三卡 prop 共綁、各卡儲存只送自己欄位（部分更新）、成功後重拉 getProfile；PasswordCard 完全自持不綁 model。
- **改密卡**：驗證方式 radio 三選（旧密码預設／邮箱验证码／手机验证码）放 NFormItem `#label` slot；切換即清空 credential＋input type password↔text 翻轉（防 shoulder-surfing）；credential 不掛 required（後端 verify 把關）；非 old 路徑保存＝toast「功能建置中」不送出。★confirm rule 必傳 `toRef(model, 'newPassword')` 非值快照（rev3 latent bug：值快照間歇 silent 失敗、curl 測不到）。
- **政策動態規則**：buildPolicyRules 把 auth-only getPasswordPolicy 的 KV 轉 naive rule（Map 化、number parseInt NaN 略過、bool `'on'` 才出規則、統一訊息單句＋trigger `['input','blur']`）；rev3 消費 6/7 鍵（漏 forbid_username、其 CHECKLIST 列為待補遺留）。
- **驗證碼佔位三處**（rev3 user 拍板、真流程需 SMS/SAML2 基建屬未來）：email/phone 卡各一組 NInputGroup（發送鈕＋驗證碼框＋驗證鈕、全 enabled、點擊 toast 建置中）＋改密卡兩 radio 路徑。
- **基本資料卡**：账号/角色/创建/修改时间唯讀 `.uc-readonly` 純文字 span（非 disabled input）；roles 全形逗號 join role code；created/updated 三態標註（`classify_operator`：None→system、==uid→self、else→admin；system/admin 帶後綴、self 無、null→「未修改」）；時間 rfc3339→`YYYY-MM-DD HH:mm:ss`；昵称 input＋性别男女 radio 可空。
- **後端 4 端點**（rev3 main.rs:198-220 獨立 auth-only Router、僅 enforce_mw 無 require_policy、免 casbin seed、operator=claims.uid、不信 body id）：getProfile（10 欄含三態語意）／updateProfile（部分更新四欄 gender/nick/phone/email、Some 才 Set、DTO 無身分欄）／getPasswordPolicy（7 鍵 allowlist 只投影 `{settingKey,settingValue}`——U2 教訓：前端借 super-only getSystemSettings 撞 403 才逼出此端點）／changePassword（固定序 notFound→mismatch→oldMismatch→tooWeak→hash→窄寫；兩處並發硬刪 no-op→notFound 防假報成功＝rev3 REVIEW F-6）。
- **rev3 明確不撤 session**（其 §I.7 明示 OUT、CHECKLIST §4.2 預告日後補）——rev4 補撤 session＝兌現 rev3 自己預告的 enhancement、非漂移。
- **rev3 已知坑（防重踩清單精華）**：F-6 並發假報成功（已修形照抄）；F-2 find_all 缺 ORDER BY；confirm rule toRef；radio 切換清空 credential；空 body `{}` updateProfile 純時戳 bump（rev3 遺留 low）；forbid_username 前端 hint 缺（rev3 遺留）。

### 0.2 rev4 落地面（D 鏡頭親驗）
- **零 migration 成立**：sys_user 欄集完整覆蓋 profile 卡全部欄位（user_gender/nick_name/user_phone/user_email＋審計四欄）；schema-gate 三閘不觸。
- **前端零工作面**：`/user-center` route、頭像下拉入口、`route.user-center`＋`common.userCenter` 三語值全已在場；**index.vue＝上游基線既有檔**（與基線 example tip 逐位元相同、7 行 LookForward 佔位頁）→改寫＝修改型 inline 需 `原行:` 逐字標；modules 4 檔＋wrapper＋typings＝新增型圈界。
- **後端可複用底座**：ADR 0054 單一驗證點 `model/password.rs::{load_policy, validate_against_policy, hash, verify}`（0054:66-67 明文自助改密 MUST 複用、禁止分叉；rev4 較 rev3 多 maxBytes 512 上界＋違規碼字面）；011 `reset_password`（sys_user.rs:1020-1089）＝keep-sid 撤 session 全形（advisory_lock_user_db→鎖內重驗→UPDATE→`revoke_others_of_user(txn, uid, keep_sid)`→逐 sid session_event(revoked, password_reset)→同 txn op-log→commit→`broadcast_revocation` 8888 best-effort）。
- **前端 8888 管線已備**：`.env:39` `VITE_SERVICE_LOGOUT_CODES=8888,8889`（靜默登出）——他裝置下次請求即登出、前端零改。
- **access_log 無密碼入日誌風險**：middleware/mod.rs:203 明文「絕不含 query string、絕不讀 body」。
- **憲法**：§III.2(g)（constitution.md:189）已授權 user-center 自助頁本體全範圍（profile 檢視／編輯＋改密＋驗證 UI 佔位、非 Casbin menu）；島 I1/I2/I5 軌道現成；ADR 0055 不變式段「改密撤他 session、保留當前操作 session」＝島 I2 在操作者=標的情境的權威釋義。**amendment 候選一筆**：(g) 字面不含「＋對應 i18n key」（(c)(d)(e)(h)(i) 五用途全明寫、對照顯著），page.userCenter.* 29 鍵屬 upstream locale inline 新增＋Schema 鏡像、超出 I18N-WIRING (ii)(iii) 僅限 backend 命名空間的射程——預告 (g) 擴字串 amendment（MINOR、照 013 v1.11.0 (d) 擴字串前例、plan 期 Constitution Check 定案）。
- **選單可達性缺口（兩庫親驗）**：casbin `p|R_SUPER|user-center|menu` 僅一列（rev3 同病未解）；rev4 dynamic 路由模式下非-super 點頭像入口＝404——本刀必解（D1）。
- **錯誤碼體系**：rev4 無 `biz.password.*` 域（grep 實證 48 鍵）；`biz.user.userNotFound` 鍵名與 rev3 `biz.user.notFound` 不同；011 已升級政策違規為 `BizData("biz.user.passwordPolicy", violations)` 明細形＋前端 `backend.biz.user.passwordViolation.*` 8 鍵三語已備。
- **throttle 模組不可直掛**（補查證僞）：007/008 節流狀態機綁死 login 流程（sys_login_attempt 計數＋captcha gate）——改密端點防舊密暴力試需另做、本刀不做（見 §3 取捨）。
- **constant route 案證僞**（補查）：soybean constant routes＝免登入層（login/404、anon 端點回傳）——user-center 需登入、放入＝治理語意錯位。

## §1 拍板（user 親決 4 題、2026-07-17）

- **D1 選單可達性＝getUserRoutes 恆附掛 self-service 白名單**：後端 getUserRoutes 組裝回傳時恆附掛寫死的 self-service 路由白名單（現僅 user-center 一項）——任何登入角色必得、新角色永不漏、零 seed migration。憲法錨點＝§III.2(g) 明文 user-center「`hideInMenu:true`、經頭像下拉入口、**非 Casbin menu**」——此頁已被憲法劃出 Casbin menu 治理域，白名單附掛＝(g) 頁級豁免在路由樹組裝層的實作；§I.2 字面「業務 menu 走 getUserRoutes → 後端 Casbin enforce 過濾 → 前端顯示」不受影響（業務 menu 過濾照舊、白名單僅補非 Casbin menu 的 self-service 頁；plan 期 Constitution Check 復核）。→ADR 0065 draft。落選：seed 全角色 menu policy（新角色漏配即 404、rev3 即此病）；constant route（已證僞）。
- **D2 改密政策違規拒因＝rev4 BizData 明細形**：toast 逐條列違規（複用 `biz.user.passwordPolicy`＋violations、passwordViolation.* 三語已備、ADR 0054 零分叉）；表單內即時驗證維持 rev3 統一單句不變。落選：復刻 rev3 單句（反向適配、與管理面體驗不一致）。
- **D3 改密成功 toast＝加撤 session 揭露**：專屬文案「密碼已更新，其他裝置已登出」（新鍵三語）——誠實揭露新後果、防使用者誤判盜帳。落選：沿 common.updateSuccess（他裝置被登出零預告）。
- **D4 forbid_username 即時提示＝補齊**：新密碼欄即時驗證補第 7 鍵（輸入與帳號同文密碼立刻紅字；userName 前端已有、違規譯文已備）——行為強化非版面變動、後端權威驗證不變。落選：嚴守 rev3 現狀（保留 rev3 自認遺留）。

## §2 工程級自拍（報備；審 spec 時可翻案）

1. 錯誤 i18n 鍵落域＝併 `biz.user.*` 既有域（新 key 如 oldPasswordMismatch／passwordMismatch；全 2222 零新錯誤碼）。
2. self 消失路徑分工照 rev3：讀端 getProfile→Internal 5000（比照 rev4 getUserInfo 同語意）、寫端→biz notFound。
3. session_event reason 沿用 `password_reset`（零詞彙表守恆測試更動；operator==target 已可鑑別自助）。
4. op-log AuditOperation reuse `ResetPassword`（payload 白名單 {id, user_name} 沿用）。
5. updateProfile 空 body `{}` 起手判全 None 提前 no-op（堵 rev3 純時戳 bump 遺留）。
6. rev3 死鍵 `changePwdBtn` 不承襲（30→29 鍵；rev3 grep 零使用處實證）。
7. 清欄回 NULL 沿 rev3 不做（空字串存 ''；feature 級另議）。
8. zh-TW 29 鍵譯文 Claude 擬全表、user 審 diff（「保存→儲存」「邮箱→信箱」「手机号→手機號碼」在地化；zh-CN 底本＝rev3 逐字）。
9. 舊密暴力試節流本刀不做＋立 BACKLOG 條目（攻擊前提＝已劫持 session；rev4 throttle 模組綁死 login 流程不可直掛；rev3 as-built 同無）。
10. wrapper／typings 命名照 rev4 慣例：`service/api/rev4-user-center.ts`＋`typings/api/rev4-user-center.d.ts`（view 直接路徑 import 不經 barrel、防 vite stale-export）。

## §3 設計（分節核可 2026-07-17）

### 3.1 整體形狀
`/user-center` 自助頁全家桶、UI 與 rev3 完全一致：單欄縱排 4 卡＋各卡獨立部分更新＋驗證碼 UI 三處純佔位照搬。後端新增 auth-only 4 端點家族 `/userCenter/{getProfile,updateProfile,getPasswordPolicy,changePassword}`（`Protection::Authed`、operator=claims.uid、不信 body id）。零 migration、零 schema 變更、零新錯誤碼、零新依賴。

### 3.2 後端
- **changePassword（主刀口）**：rev3 固定驗證序（notFound→兩次不一致→舊密不符→政策違規）＋rev4 補撤 session。時序照島 I2/I5 合規範式（島 I5：「密碼雜湊 MUST NOT 於持有列鎖期間計算」；島 I2 登入款範式：「純比對不重跑雜湊」）：**鎖外**預讀列＋舊密 verify（argon2）＋政策驗證＋hash 新密→txn｛advisory_lock_user_db（島 I1 與 login/refresh 共鎖）→鎖內 `find_active_by_id_for_update` 重讀＋**phc 純字串比對**重驗（與 verify 所讀一致、不重跑雜湊；已變＝舊密已失效→誠實拒 oldMismatch）→UPDATE password＋updated_at/by→revoke_others_of_user keep claims.sid→逐 sid session_event(revoked, password_reset)→op-log（password redacted）｝→commit→broadcast_revocation 8888 best-effort；鎖內查無→notFound 防假報成功。
- **政策驗證**＝ADR 0054 單一驗證點零分叉；拒因＝D2 明細形；舊密不符／兩次不一致＝biz.user.* 新 key（2222）。
- **getPasswordPolicy**：7 鍵 `password_*` allowlist 只投影 `{settingKey,settingValue}`；allowlist 與 load_policy 鍵名同源常數（防兩處字面漂移）。
- **getUserRoutes 恆附掛**（D1）：self-service 白名單寫死常數（現僅 user-center）；附掛在 casbin 過濾之後、組裝回傳前；ADR 0065。
- **facade 三支新建**（rev4 無對應物；rev3 對應物受控參照不拷貝）：`get_own_profile`／`update_own_profile`（★島 I1：以既有使用者為標的之更新寫端 MUST 交易起手 advisory_lock_user_db＋lock-then-redecide、照 011 update 寫端範式——rev3 無此鎖不可照抄；窄寫四欄、未帶 Unchanged、空 body no-op、同 txn op-log）／`change_own_password`；兩處並發硬刪 no-op→notFound 防假報成功。user_gender wire 形採 rev4 admin 面同款 `wire_enum12`（字串 1/2、值域外一律 None 不動）——rev3 裸 i16 形會繞過 rev4 自家 1/2/null wire 不變式、不照抄。
- **router**：ROUTES 註冊表加 4 筆 `Protection::Authed`＋case_key（缺 case 即紅）；access_log_mw／ip_gate 自動覆蓋。

### 3.3 前端
- 4 卡逐項復刻 rev3 藍本（§0.1）＋三處行為增補：forbid_username 第 7 鍵即時提示（D4）、改密成功專屬 toast（D3）、其他三卡沿 common.updateSuccess。
- fork-delta：index.vue 修改型 inline（基線 7 行佔位頁、原行逐字標）；modules 4 檔＋wrapper＋typings 新增型圈界；每改即跑 `python3 tools/fork-delta-lint`。
- i18n：`page.userCenter.*` 29 鍵三語新建＋`App.I18n.Schema` 型別鏡像同步；`route.user-center` 三語已備零工作；前端「兩次輸入密碼不一致」（form rule）與後端拒因鍵並存勿混併（rev3 兩鍵字面即不同）。

### 3.4 治理・測試
- 憲法：頁本體零 amendment（§0.2 實證）＋**(g) 擴字串 amendment 候選一筆**（＋對應 i18n key 用途補完、詳 §0.2、plan 期 Constitution Check 定案）；新 ADR 一份（0065 self-service 路由恆附掛、draft 隨本檔同 commit）。
- 測試：rev3 純測藍本照抄（classify_operator 三態＋政策邊界＋verify/hash roundtrip＋redact 斷言）＋**新增 keep-sid 語意測**（本 sid 存活、他 sid 撤、廣播 8888——rev3 無此測可抄）＋getUserRoutes 白名單兩向測＋resolve_home 交互案（零 menu policy 角色 home 兜底落 user-center＝新行為、明載）＋契約 case 4 筆＋負向自證候選（①撤 session 拆除即紅②政策驗證走單一驗證點、拆分叉即紅）。
- CDP 驗收：四卡 UI 逐項對照 rev3 實機快照＋三語零 raw key＋**非-super 帳號實測**（選單可達＋改密全流程；探索期僅測 Super）。

### 3.5 明確不做與殘餘風險（設計取捨）
- 驗證碼真流程（SMS/郵件基建）——僅佔位 UI 照搬；**佔位非安全機制**（後端契約僅認舊密路、crafted request 無驗證碼路徑可走）；接通屬未來刀。
- 舊密暴力試節流——自拍 9、立 BACKLOG。
- **keep-sid 殘餘風險（誠實記載）**：改密必收舊密——僅劫持 session 不足以改密，舊密 gate 即既有防線；若攻擊者兼知舊密，其反鎖真主人的能力與 keep-sid 無關（可另行登入再改）＝keep-sid 非使能因子。緩解＝他裝置 8888 靜默登出屬異常訊號、復原路＝admin resetUserPassword（operator≠標的時全撤含攻擊者 sid、B-029 主路）。
- 清欄回 NULL——自拍 7。
- B-030 首登強制改密——下一刀（本刀落地即解鎖其觸發條件、ADR 0055）。
- 郵箱/手機「已綁定值」顯示強化、頭像上傳等 rev3 沒有的功能——零新增（YAGNI）。

## §4 遺留註記（進 specify 前已知）

- SYNTH 缺口 1/2/3/7（rev4 password_* 鍵名字面對齊、ROUTES case_key 慣例、user-operate-drawer violations 渲染形複用、session_event 常數區）＝plan 期接地項、不擋 spec。
- 探索報告全文（五鏡頭＋SYNTH）存 session scratchpad（暫態）；本檔已萃取施工必需精華、rev3 細節以其 repo 源碼為權威（本機受控參照）。
