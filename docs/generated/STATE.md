<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=cced2fd｜rust-api=22f3744

## constitution
- 版本：1.13.0

## 帳面統計
- ADR：66（accepted 61、superseded 5）
- BACKLOG 待辦：43（next：B-105）
- LESSONS：145 筆（next：L-148）
- events：18 筆（feature_close 14、misc 3、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-17｜misc｜B-104 頁面切換 Transition 上游卡死 workaround 收刀（輕量軌第二例、user 拍板改提前施工＋跳過 SDD）。根因＝Vue BaseTransition（global-content 之 Transition mode=out-in＋KeepAlive）快速連續導航 race 使 state.isLeaving 卡 true、main 永久空渲染（點 tab/menu/內建刷新全無效、僅整頁 F5 可復原）；CDP 診斷證據鏈逐項消去（route 正常／reloadFlag true／關動畫仍空／reloadFlag toggle 救不回／contentXScrollable 恆 true 煙槍）＋新分頁 80ms 連打 14 次穩定重現（40ms 不中＝須正中 fade-slide 300ms leave 窗）；歸屬上游（global-content 上游原檔零 fork 改動、Vue 3.5.34、rev3 同構同病）。修法（user 親決、spike 三案實證後擇一）＝去 mode=out-in（isLeaving 路徑根除）＋fade-slide leave 側拆規則 absolute 化（main:has 相對定位＋left-gap 變體以 --soy-sider-width 補 padding box 錨定差、交疊淡出零版面跳動）。治理＝憲法 v1.13.0 新用途 (j) layout 上游缺陷修補（嚴格限有重現法之上游缺陷、一案一 ADR、本刀首案）＋ADR 0066 accepted（含候選落選與殘餘：其他 animateMode 未 absolute 化 by-design、upstream rebase 時覆核）。品質＝Workflow 單元（implementer→spec/quality 雙審 fix 迴圈、7 agents）＋主線 CDP 雙驗證（80/60/120ms 連打全綠卡死指紋不現＋轉場交疊期 offsetLeft/Top/Width 完全同位）＋typecheck/fork-delta-lint 綠（兩檔修改型原行逐字標）。流程註記：看門狗首掛被 U8 殘目錄搶答（L-144 實證第二例、TaskStop 重掛即正）。
- 2026-07-17｜feature_close｜014-user-center｜個人中心自助頁收刀——B-090 自助改密兌現＋rev3 025 全頁承襲；rev4 首個 auth-only 業務端點家族 /userCenter 四端點（Protection::Authed、operator=claims.uid 不信 body id）。US1 改密全鏈＝固定驗證序五拒因（userNotFound→passwordMismatch→oldPasswordMismatch→passwordSameAsOld→passwordPolicy 明細、全 2222 零新碼）＋keep-sid 撤他裝置（revoke_others keep=claims.sid＋session_event(revoked,password_reset) 逐筆＋8888 廣播 best-effort、facade 回 sids 廣播歸 handler 照 reset_password 分層）＋島 I1/I2/I5 合規時序（argon2 verify/hash 全在鎖外 txn 外、鎖內 phc 純字串比對、advisory_lock_user_db 共鎖 lock-then-redecide、並發測附 pg_locks 等待者斷言）＋「新≠舊」端點固有規則不入 ADR 0054 單一驗證點（負向測拆分叉即紅）＋密碼三重不洩（ChangePwdReq 手寫 Debug 三欄全遮／op-log payload {id,user_name} 白名單／getProfile 零密碼零會話識別）。US2 profile＝get_own_profile（roles join 成員口徑＋classify_operator 遷居 facade 三態折疊 system/self/admin、OwnProfile 白名單型結構性不洩 operator uid）＋update_own_profile（島 I1 鎖＋窄寫四欄 Some 才 Set＋全 None txn 前 no-op 零時戳＋同 txn op-log）＋wire_enum12/i16_to_wire pub(crate) 化同源複用；三卡部分更新零串擾。US3＝SELF_SERVICE_ROUTES 白名單恆附掛（casbin 過濾後 HashSet 聯集去重、resolve_home 與 casbin 過濾零改動、零 policy 角色 home 兜底落 user-center 新行為測試明載；ADR 0065）＋index.vue 修改型 inline 改寫（基線 7 行原行逐字標、rev4 首例基線佔位頁改寫）四卡組裝（PasswordCard 自持僅收 userName prop、三卡 model 共綁 @saved 重拉）。US4 三語＝page.userCenter 31 鍵（29 承襲 rev3 逐字＋D3 changePwdSuccessRevoked＋D2 統一單句 pwdPolicyNotMet〔實作期盤點缺口、U4 spec-review 抓獲、user 親決 A 案補鍵＋spec 五處量詞勘誤 30→31〕）＋biz.user 3 拒因鍵＋App.I18n.Schema 鏡像機器證＋U8 全表審校（zh-CN 29 鍵 rev3 逐字 diff 零差、機器對帳）。治理：憲法 v1.12.0（(g) 擴 i18n key 字串＋島 I2 keep-sid 釋義、ADR 0053 偏差句以 0055 為準）＋ADR 0065 accepted（GATE 提前親決、實作期治理級親決一次〔D2 鍵落點〕）；零 migration／零 schema／零 seed／零新錯誤碼／零新依賴／零新島（自助域＝島 I 操作者=標的變體）。品質：TDD 九執行單元（U1~U8 Workflow 各 implementer→spec/quality 雙審 fix 迴圈、全 agent 繼承 Fable；U9 主線親跑）全綠——cargo --lib 685＋workspace 16 suites 零 failed＋contract registry 63→67＋wire_schema 10＋typecheck/fork-delta-lint 綠＋負向自證二條（keep-sid 拆撤銷即紅／零分叉拆即紅）；CDP S1~S6 全 PASS（零 policy 帳號進頁不 404＋home 兜底實測／雙 session keep-sid 本 sid 0000 他 sid 8888 實彈＋D3 toast 揭露句／拒因四類實彈＋violations 三碼齊發明細／佔位三處 comingSoon 且 POST 計數=0＋credential 清空 type 翻轉／三卡部分更新零串擾＋三態後綴（系統建立）（未修改）self 無後綴／三語切換零 raw key）、cdp014 測試資料八表殘留歸零＋政策鍵還原。U9 抓獲 D4 比對源錯位真 bug（authStore.userInfo.userName＝sys_user.nick_name 別名〔憲法 L45 getUserInfo 投影〕、以暱稱比對輸入真帳號不觸發）→prop 化修復（T012 字面預授權例外）＋CDP 複驗紅字實彈。final review 雙 Opus 零 merge-blocker（三分流：修 0、B-103 轉列、備查 3〔恆送兩欄=rev3 承襲／圈界世代差=v1.12.0 by-design／guard 診斷訊息 prefix 純測試診斷〕）。
- 2026-07-17｜misc｜settings 頁 tooltip 三語化收刀——B-059 兌現（004 單元⑧遺留）。IconTooltip 直顯 DB seed 繁體 description → page.manage.systemSettings.help 15 鍵三語鍵化（zh-TW 逐字 seed description、zh-CN/en 術語對照翻譯）＋App.I18n.Schema help 段鏡像＋index.vue helpKeyMap/helpOf 房式照 labelKeyMap（typed literal、未映射 fallback description、皆無回空字串）、IconTooltip 改綁 helpOf。零後端零 migration 零 schema、DB 不動；I18N-WIRING (ii)(iii)、ADR 0041 射程內用途補完、零新 ADR。品質：Workflow 單一執行單元（implementer→spec 合規＋code-quality 雙鏡頭 review 各一輪即綠、零 blocker、共 3 agent）；typecheck＋fork-delta-lint 綠；CDP 三語實機全 PASS（15 icon 全渲染、零 raw key、zh-TW 逐字＝DB seed、hover 實彈＝字典值）。流程：輕量軌首例——BACKLOG 小刀跳過 brainstorm＋SDD 五步（user 拍板 2026-07-17）、驗收依據＝BACKLOG 條目重偵察結論；feature branch 用 b059- 前綴（不佔 NNN 序列、留給 SDD 刀）。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
