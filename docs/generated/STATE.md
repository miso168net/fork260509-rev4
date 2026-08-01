<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=ec6ca69｜rust-api=a07061a

## constitution
- 版本：1.15.0

## 帳面統計
- ADR：87（accepted 81、superseded 6）
- BACKLOG 待辦：28（next：B-133）｜滯後：3
- LESSONS：200 筆（next：L-201）
- events：45 筆（feature_close 20、misc 22、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-08-02｜misc｜B-045＋B-018 空集合條目結清（簿記面、user 認可；無工程項、零程式改動）——①B-045 低位殘項 checklist 四子項逐項驗證全落空：XFF 空 token 已由 trust/mod.rs normalize_xff 之 filter(!tok.is_empty()) 收（含 hostile 字串全丟棄斷言）；計數 race 隨 ADR 0037 合成終態架構性消失（sys_login_attempt append-only、零 fail_count/counter 欄＝無 read-modify-write 面）；migration down 非對稱證偽（15/15 檔全實作 async fn down、grep -L 零缺漏；down→up 往返之已知 id 前移偏差早載 schema-gate.py 檔頭）；CDN 錨與 B-080 完全重複（該條在架、留獨立 ingress 硬化刀）；trace_id 控制字元子項條目自述已由 016 sanitize 單一 seam 收單。②B-018 帳號級鎖定被第三方惡意鎖人的 DoS 面重估結清：候選緩解手段全數已有 ADR 歸屬——已落＝007 三層（captcha 軟區抬自動化成本／unlockLogin 手動解鎖／鎖存續≤window 自解）＋008 IP 白名單跳節流（U11）；won't-do 三項各載 ADR 0037 §H 且逐項以 B-018 為理由（24 漸進延遲＝sleep 持有連線槽、攻擊者可並行繞過、懲罰合法手滑者；26 音訊驗證碼＝一旦提供即成 B-018 緩解的普遍後門；27 帳號級 captcha 豁免旗標＝可探測後對最需保護帳號免摩擦鎖人、且加欄破零結構變更）；ADR 0038 另以「延長鎖只傷受害者、正是 B-018 惡意鎖人要治的病」為負快取設計約束。per-user 觸鎖殘餘＝ADR 0037 節流架構的必然推論、非新拍板，故不新立 ADR（結清理由與血緣即本筆）。③同批第三項 B-113 條目病因勘誤改寫已於 maint-lint-speedup-rename 同刀完成（見本日 lint 刀事件筆），本筆不重複。BACKLOG 待辦 30→28（next 仍 B-133、號碼永不回收）。
- 2026-08-02｜misc｜lint 提速＋條款編號改名收刀（maint-lint-speedup-rename、merge a656b834；user 拍板 lint-ok、兩單元序做）——①u1 提速：lint 條款 close_existence 慢路徑「逐慢路徑 id 各發一次 git log -S pickaxe（單發約 7s、隨收刀線性累積）」改至多一次全史單掃建曾存在 token 集合（cache 參數區域下傳照 submodule_head 慣例、lazy 零慢路徑 id 零成本）；lint 123.6s→14.6s、pre-commit 全鏈 104.6s→15.7s（對照 018 T001 基線 46.4s 之 2.2 倍劣化根治、成本 O(已刪條目數)→O(1)）；等價性＝三型 id fixture 雙法對照案＋審查側 300 id 全面對照零 mismatch＋新舊版 lint stdout 位元組級全等；雙審 minor 修繕＝--no-color/--no-ext-diff/--no-textconv 免疫 git 組態（color.ui=always 實測 token 集塌空）＋B-888 標題行注入突變守護＋memo 區域化。②u2 改名：條款編號 L1~L22 全面改名 Lint01~Lint22（兩碼零填＝user 拍板；消 LESSONS L-NNN／throttle 快取層 L1/L2／憲法行號引用三套同形記號混淆）——本體 tools/docs-sync.py 約 389 token＋活文件 34 處（RUNBOOK 16＋CLAUDE.md 1＋ARCHITECTURE 3＋LESSONS 三卷 10＋pre-commit 4）；前置修正 RANGE_CODE 切片 removeprefix 化（原 [1:] 硬切改名即 ValueError 崩）；Lint22 守衛原子耦合（RE_LINT_CODE/RE_RANGE 拆分構造保留、範圍字串四處數值形＋一處泛形一律 Lint03～Lint23）；新增 Lint23 舊碼禁令（語料 OLD_CODE_CORPUS 四檔＝三活手冊＋.githooks/pre-commit、值域 1~22 字界、紅綠 self-test＋實彈紅證；史料 162 處與 events 26 處依時態分離判例明文不動）；accepted ADR 六處加註形 L16 (Lint16)（0077/0078/0082、[adr-amend]＋DOCS_SYNC_ADR_AMEND=1 由主線親做、Lint08 豁免通道實證）；雙審 minor 修繕＝兩碼零填機器守衛（scan_nonpadded_codes＋防恆綠案）＋Lint23 語料擴 pre-commit（連兩例漏改實證最弱環）＋self-test 補兩碼分支＋誤紅出路訊息（節流 L1/L2 誤紅時勿照打換碼）＋LINT02_SOURCES 大小寫歸一；B-113 條目病因勘誤改寫（drvfs git init 與 73ms 斷言證偽、原三候選瞄錯靶、真熱點已由 u1 收）。驗證＝396 案全綠＋lint 0 錯 0 警（輸出碼面全 Lint 兩碼形）＋check 一致＋負向 grep 白名單全達。過程要點：classifier 對 workflow 內寫檔實作派發 session 級固化攔截（u1/u2 implementer 皆經 user 逐段授權直派；唯讀 review 型 workflow 可通過＝u2 雙審以 workflow 姿態完整收斂零 blocker）。commits＝4957a58+d677368（u1）/6da998a+d53ca34+e75bd42（u2）。
- 2026-08-02｜misc｜B-101 全收收刀（maint-b101、merge 7994b68；user 拍板 gogogo、workflow 編排＋雙審 Opus xhigh）——①一致性檢查（TDD 先紅）：新整合測試 button_consistency 斷言 casbin_rule v2=button 碼集＝sys_menu 活列（deleted_at IS NULL、與消費端 all_button_codes 之 list_governed 治理域逐字對齊）buttons code 聯集、失敗印兩方向差集＋空集 fail-loud 前置；現況紅證恰四碼（user:reset-pwd/kick/restore/unlock、反向空集）。②m015 回填（轉綠）：manage_user.buttons 三碼原值原序＋append 四碼（序＝m008 seed 登記序；desc 簡體照 m010 定論、出處 base-web zh-cn 字典、restore 比照欄內動賓構詞自擬「复原用户」）；冪等＝整值置換、down＝整值還原 m002 三碼原值；down/up 負向自證紅綠序全程實測（down 後檢查紅＋gate2 override 軌 FAIL＝雙防恆綠實證）。③ADR 0064 軌道登記：SEED_CONTENT_OVERRIDE_ALLOWLIST 新登記 (sys_menu, route_name=manage_user, buttons) 七碼＋留痕（首筆 m010 形制；外層與 pin 同筆收單＝m010 同 commit 登記先例）。驗證＝button_consistency 綠＋lib 772 零回歸＋gate1/gate2/audit PASS 差異 0＋schema-gate test 134。過程要點：spec 審中揪出 gate2 既存髒資料（Admin.user_email=admin@test.local、020 期 UI 實測殘留、時序早於本刀三小時）→user 拍板還原 NULL（衛星表驗證史保留）、明令勿登 allowlist（違 ADR 0064 本意）；classifier 三攔 workflow review 派發→user 明確授權直派品質審（Opus 唯讀）＝放行 0 blocker 2 minor（檔頭 triage 說明已補 a07061a、m015 未濾 deleted_at 判 won't-fix＝m010 同形貼風格＋已套用不改）。五源互比（up SQL＝allowlist＝實庫＝m002 字面＝凍結 fixture）全 True。rust-api pin 2db1324→a07061a（3118e59 檢查紅＋b05b799 m015 綠＋a07061a 檔頭 triage）。B-101 條目完成即刪。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
