<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=b2c6e56｜rust-api=fd4c405

## constitution
- 版本：1.10.0

## 帳面統計
- ADR：60（accepted 55、superseded 5）
- BACKLOG 待辦：51（next：B-096）
- LESSONS：142 筆（next：L-143）
- events：13 筆（feature_close 11、misc 1、review 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-14｜review｜001-010 全量 as-built spec 合規性（wf_5e6d9105-d04、10 review＋2 adversarial verify）
- 2026-07-14｜feature_close｜011-user-admin｜使用者管理與使用者域狀態機收刀（admin 家族第三刀；使用者域端點全新地＋六刀遞延承諾兌現）。核心＝島 I 五條入憲 v1.9.0（I1 統一序列化＋固定鎖序〔advisory(uid) 與 login/refresh 共鎖、user→role 升序→指派禁反向、lock-then-redecide、addUser 豁免〕／I2 撤銷連動同交易＋權威優先＋★B1 login 鎖內重驗〔status∧未刪∧雜湊純比對、不符中止 1000 恰一列稽核＋計節流窗；run_refresh 合法撤銷 denylist reason=revoked→靜默 8888 零 reuse〕／I3 seed 結構保護〔三帳號不可刪、Super 恆禁停用/解超管、self 四不〕／I4 硬刪指派＋復原零回灌＋status 保留＋批刪 fail-fast／I5 密碼政策單一驗證點＋三重不洩）。US1 CRUD＋指派寫端（B-084 兌現：sys_role 升序鎖＋鎖內重驗、未知/已刪 code 整批拒；停用角色可指派）＋user_name 零正規化＋diff no-op〔NULL≡""、Some("")=清空〕＋帳號名不可變＋同名重建零繼承。US2 kickUser（鎖列未刪即可＝停用可踢、Super 可踢）＋四路撤銷 reason 映射（user_disabled/user_deleted/admin_kick/password_reset；session_event 同交易 PG-first→denylist best-effort、★TTL=refresh_secs；8888/7777 不互換）＋併發④撤銷×並發登入。US3 resetUserPassword（政策驗→hash 鎖前算→撤 token〔operator keep 當前 sid〕；★不解節流機器證；payload 恰 {id,user_name}）＋密碼政策 7 鍵單快照首度真實執行（chars＋bytes 512 上界、forbid_username 大小寫不敏感、violations 8 碼明細）。US4 回收桶（deleted_at DESC＋restore 鎖內同名重驗＋23505 兜底、零回灌、status 保留、不 bump updated_at；partial-uniq 索引斷言）。US5 session_policy（值域 txn 前驗＋no-op；改 single 不即時踢）。US6 解鎖 UI（unlock modal 雙維 net-new、fetchUnlockLogin 補建、B-061 note 兌現）。US7 i18n（biz.user 15 鍵＋unlock 2 鍵＋passwordViolation 8 子鍵＋page.manage.user 24 鍵三語＋Schema 同 commit；violations 先譯後 join 成 scalar 插值）。前端接線 v1.9.0 四處擴展逐處對號零超界：ADAPT/WRAPPER 9 fetcher＋index.vue（接真＋hasAuth 七碼＋回收桶＋解鎖鈕＋kick/reset）＋drawer（密碼欄＋政策 hint＋userName 鎖定＋session_policy 現值 diff 觸發）＋pwd-login 放寬〔LOGIN-CAPTCHA (ii)〕。治理：憲法 v1.9.0＋ADR 0053/0054/0055；m008 純 seed 8 列（allowlist 同 commit）；零 schema/零新錯誤碼/零新依賴。14 執行單元全 TDD＋雙審查（U9 起 review/fix 用 Opus 4.8 1m）；負向自證七條拆除轉紅實證＋併發機器證 4 組＋契約 registry 48→58 雙射。cargo 624 綠（基線 528、既有零轉紅）；gate2 244/244；typecheck/fork-delta-lint/docs-sync 綠；CDP S1~S6 全 PASS（雙 session 8888-7777 分流、no-op 時戳機器證、17 拒因鍵三語零 raw key）、cdp011_ 殘留歸零、負向登入僅 3 次。final review 雙 Opus 零 merge-blocker（三分流：userName errata×3〔adr-amend〕、B-088/B-089、L-140/L-141）。
- 2026-07-13｜feature_close｜010-menu-admin｜選單管理與選單域狀態機收刀（admin 管理面家族第二刀；把基線預埋的選單域 7 端點接成活的）。核心＝選單域 advisory 序列化域（島 H1）＋治理域·顯示域分層（H4）＋同鍵重建零繼承雙封（H2）。US1 選單生命週期：CRUD 5 端點（getMenuList/v2〔GET〕/addMenu〔POST〕/updateMenu〔POST〕/deleteMenu〔DELETE〕/batchDeleteMenu〔DELETE〕）＋域內固定序〔advisory 首動作→FOR UPDATE→鎖內重驗→寫→連動歸檔→op-log→commit〕；addMenu route_name 守門〔^[A-Za-z0-9_-]{1,100}$〕＋parent 三態驗〔未刪即可/停用不擋/parentId=0 豁免〕＋23505 收斂 routeNameExists＋★零 casbin 寫（兩步流 FR-004）；updateMenu 無變更 no-op＋不可變欄雙鍵〔routeName/menuType 比對現值〕＋re-parent 環檢測〔上溯遇 self、上限 64〕；deleteMenu 守門①protected→②hasChildren〔含停用子〕＋同交易連動歸檔〔menu 維跨全角色＋獨有 button 維 reason=menu_soft_delete〕；batchDeleteMenu 自管 txn＋去重＋樹深 DESC child-first 拓撲序＋no-partial。US2 刪除不留幽靈授權：★同鍵重建零繼承雙封（現役序列化域無殘留＋歸檔 reason gate 不可回灌）；updateMenu buttons 絕版連動〔移除 code 全域絕版→archive-move reason=menu_button_removed→Applied 才 reload〕；併發機器證三組〔deleteMenu×updateRoleMenu／對向 re-parent／deleteMenu 父×restoreMenu 子〕以 wait_advisory_waiter 觀測 advisory 序列化、終態序列化。US3 回收桶：getDeletedMenus〔GET protected〕平面 deleted_at DESC＋restoreMenu〔POST protected〕7 步序〔advisory→鎖已刪列 find_by_id_for_update→鎖內重驗同鍵活性衝突〔routeNameExists+23505 兜底〕/parent 未刪驗→成對清空 deleted_at/by→op-log Restore〕＋★零回灌授權（FR-023）。US4 兩域分層：治理域〔未刪含停用 list_governed〕換源四處〔getMenuTree/getRoleMenu 反查/getAllButtons/menu_id↔route_name〕使停用選單仍在授權候選、全量替換不誤撤〔停用≠撤銷 FR-019〕；顯示域〔啟用∧未刪 list_active〕getUserRoutes/getAllPages 停用即隱、restore 即回（FR-018/032、不動）。US5 拒因結構化明細：backend.biz.menu 十鍵三語〔皆 scalar、biz.policy.notRestorable 復用〕、onError translateBackendMsg 渲染、無 raw key。前端：建檔一對 ADAPT/WRAPPER 6 fetcher＋modal/index.vue 接線＋hasAuth＋回收桶 toggle/restore＋edit parentId NTreeSelect；fork-delta 原行紀律。治理：新島 H 入憲 v1.8.0〔H1 選單域序列化＋H2 同鍵重建零繼承＋H3 樹不變式＋H4 兩域分層＋H5 復原不回灌〕＋§III.2(d) 錨點擴充＋ADR 0051/0052；零新錯誤碼/新表/seed/依賴。12 執行單元 U2-U13〔U12 全量閘＋CDP、U13 簿記〕全 TDD＋雙審查迴圈＋主線 load-bearing 自驗。cargo test --workspace 478 綠；gate2 244/244＋typecheck＋fork-delta-lint（基線 example@8be6f9ba）綠；5 負向自證（①protected②環檢測④batch no-partial③刪除連動⑤絕版）＋3 併發機器證 standing 綠；CDP 實機（Edge@9229）S1 CRUD/兩步流、S3 回收桶 toggle-restore、S4 停用分層、S5 拒因十鍵三語零 raw key PASS、殘留零污染。

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
