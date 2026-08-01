<!-- 機器生成：tools/docs-sync.py generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=ec6ca69｜rust-api=a07061a

## constitution
- 版本：1.15.0

## 帳面統計
- ADR：87（accepted 81、superseded 6）
- BACKLOG 待辦：30（next：B-133）｜滯後：3
- LESSONS：200 筆（next：L-201）
- events：43 筆（feature_close 20、misc 20、review 3）

## 最近事件（尾 3 筆、新在前）
- 2026-08-02｜misc｜B-101 全收收刀（maint-b101、merge 7994b68；user 拍板 gogogo、workflow 編排＋雙審 Opus xhigh）——①一致性檢查（TDD 先紅）：新整合測試 button_consistency 斷言 casbin_rule v2=button 碼集＝sys_menu 活列（deleted_at IS NULL、與消費端 all_button_codes 之 list_governed 治理域逐字對齊）buttons code 聯集、失敗印兩方向差集＋空集 fail-loud 前置；現況紅證恰四碼（user:reset-pwd/kick/restore/unlock、反向空集）。②m015 回填（轉綠）：manage_user.buttons 三碼原值原序＋append 四碼（序＝m008 seed 登記序；desc 簡體照 m010 定論、出處 base-web zh-cn 字典、restore 比照欄內動賓構詞自擬「复原用户」）；冪等＝整值置換、down＝整值還原 m002 三碼原值；down/up 負向自證紅綠序全程實測（down 後檢查紅＋gate2 override 軌 FAIL＝雙防恆綠實證）。③ADR 0064 軌道登記：SEED_CONTENT_OVERRIDE_ALLOWLIST 新登記 (sys_menu, route_name=manage_user, buttons) 七碼＋留痕（首筆 m010 形制；外層與 pin 同筆收單＝m010 同 commit 登記先例）。驗證＝button_consistency 綠＋lib 772 零回歸＋gate1/gate2/audit PASS 差異 0＋schema-gate test 134。過程要點：spec 審中揪出 gate2 既存髒資料（Admin.user_email=admin@test.local、020 期 UI 實測殘留、時序早於本刀三小時）→user 拍板還原 NULL（衛星表驗證史保留）、明令勿登 allowlist（違 ADR 0064 本意）；classifier 三攔 workflow review 派發→user 明確授權直派品質審（Opus 唯讀）＝放行 0 blocker 2 minor（檔頭 triage 說明已補 a07061a、m015 未濾 deleted_at 判 won't-fix＝m010 同形貼風格＋已套用不改）。五源互比（up SQL＝allowlist＝實庫＝m002 字面＝凍結 fixture）全 True。rust-api pin 2db1324→a07061a（3118e59 檢查紅＋b05b799 m015 綠＋a07061a 檔頭 triage）。B-101 條目完成即刪。
- 2026-08-01｜misc｜治理工具維護批收刀（maint-b112-b128-b129、merge 1c17763；三條 BACKLOG 一次收、雙 workflow 編排＋雙審 Opus xhigh、user 拍板③全範圍）——①B-128 wire-schema 快照 drift 閘：check 子命令（重抽暫存與工作樹快照 byte 比對；容器不可用→跳過印警告 rc=0＝user 親決、容器可用但抽取失敗→rc=2 fail-loud 防恆綠洞；入口無條件 self-test 照 fork-delta-lint 形）＋pre-commit 接閘（staged 含 base-web gitlink 時跑 check --staged-gate、typings 收窄判定在 py 內＋對 base-web 跑 git 前 GIT_* env 清洗照 fork-delta-lint 模式）；TestGateWiring 三組期望拆開釘新閘＝閘接線唯一守衛（突變實測拔閘行→3 案紅、主線親證復現）；驗證＝wire-schema test 27 案＋docs-sync test 384 案全綠＋實彈 check rc=0（106 definitions）＋快照竄改一 byte rc=2 紅證（主線親做、還原後樹淨）。②B-112 rust-api 治理工具舊名勘誤十行（wire_schema.rs 行 2/30/57/284/303/304 六行＋m008~m011 各一；行 30×303 為 panic 訊息×assert 判準成對載體、負向自證先紅後綠；specs 等 8 個史料檔依時態分離明文不動）。③B-129 寄信觀測回歸保護：test_support 由 cfg(test) 擴為 lib 非 cfg(test) pub 測試 seam（照 mailer::stub_transport 先例、內層 mod tests 補 cfg(test) 防測試碼進 production 編譯）＋t022 加 WarnCapture 欄位面斷言（target security.throttle、degraded=emailverify_smtp、error_kind=connection——thread-local 捕捉過 axum oneshot 假設實證成立）＋smtp_error_kind 抽純函式 error_kind_from_flags 六分支＋順序語意（timeout 優先）測全＋lettre 0.11.22 公開 API 三真實例（client/tls/connection、零網路；timeout/permanent/transient 無公開構造路徑由純函式測覆蓋）；lib 767→772、email_verify 14、wire_schema 12 全綠。④B-132（320px 頁首溢出）user 拍板移滯後卷。過程要點：wf2 兩度被 safety classifier 攔——第一次 status 語意誤填致誤升級、主線一度放寬判斷被攔後改回 §9『failed 即 escalate』硬規則、語意修在 review prompt 源頭；第二次 quality:r2 確認輪連坐誤攔、workflow escalate 回主線後由主線親核六筆 findings 收單（血緣：quality r1 抓到 docs-sync 打紅 blocker、fix commit ec05c3e 修復）。rust-api pin bcd0496→2db1324（B-112 勘誤 3c19c61＋B-129 85edbd9＋雙審 minor 修繕 2db1324）。
- 2026-08-01｜misc｜mailpit host 配號歸位（維護輕量軌、user 收刀後質詢觸發）——020 引入 mailpit 時 host 配 127.0.0.1:8025、為 reference/ports 全表唯一不帶 4 字頭者，違反 ADR 0019 之 infra 群「4＋well-known」制（grafana 43000／loki 43100／prom 49090／pushgateway 49091／pg 45432／redis 46379 逐項遵守）。成因三段追溯：①SDD 期六產物（research/spec/plan/data-model/contracts/quickstart）直抄 mailpit 官方預設值 8025、全程無人以 ADR 0019 對照 ②U1 唯讀偵察確實示警「配號須避開此表、需 U1 決策」、衝突被機器發現並傳到主線 ③主線裁錯＝選「照 SDD 字面走」並烤進 implementer prompt，且於 review prompt 列「勿翻案」封死質疑通道。歸位＝host 48025（容器內側 8025 官方預設不動、ADR 0019 明定；tests 走服務名 mailpit:8025 與 host 正交零改動）；ADR 0087 accepted 承載配號歸位＋★判例「SDD 產物與既有 accepted ADR 衝突時 ADR 優先、MUST 升級 user 拍板、不得主線自行選邊或封死 review 質疑通道」；ADR 0086 body 依 accepted 不可變不動。驗證＝compose config 綠／mailpit 重建 healthy／48025 readyz 200／舊 8025 refused／容器內 email_verify 14 passed。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
