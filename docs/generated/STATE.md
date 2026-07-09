<!-- 機器生成：tools/docs-sync generate——嚴禁手改；差異由 pre-commit check 攔下 -->
# STATE — 現況機器帳

## git
- default branch：rev4-admin-root
- pins：base-web=338e8ba｜rust-api=3b54d06

## constitution
- 版本：1.3.0

## 帳面統計
- ADR：36（accepted 34、superseded 2）
- BACKLOG 待辦：51（next：B-072）
- LESSONS：115 筆（next：L-116）
- events：7 筆（feature_close 6、misc 1）

## 最近事件（尾 3 筆、新在前）
- 2026-07-06｜feature_close｜006-session-lifecycle｜會話生命週期收刀（波1第三功能刀、auth family 第二把、B-021 一次設計完整）：DB-stateful 化 supersede ADR 0030 無狀態方向。11 執行單元＋2 remediation——U1 redis 1.3.0 起手＋m004(partial UNIQUE uq_sys_token_chain_active＋session_event 變體B)＋AppState ConnectionManager；U2 token_hash SHA-256＋TTL refresh=N×60+access(supersede 0030);U3 sys_token/session_event/sys_user facade(rotate/revoke_family loop-until-0-active/revoke_others/has_active_in_chain);U4 redis client(denylist/last_activity/grace、Ok(None)≠Err 分流 R7)＋enforce denylist 前置(7777/8888、PG fallback fail-closed);U5 US1 refresh rotation 狀態機(FOR UPDATE lock-then-redecide L-075)＋reuse fail-secure＋grace 冪等＋partial UNIQUE＋FR-016 反轉;U6 US2 single-session(advisory lock＋effective_single＋revoke_others＋login insert active 補斷鏈)＋refresh kicked→7777;U7 US3 /auth/logout(refresh 身分、冪等);U8 US4 精確 idle(last_activity 僅 valid-access 推進、島D2/D3 降級不誤踢);U9 US5 session_event 4 類稽核;U10 refresh-time prune＋gates;U11 base-web LOGOUT-UX-WIRING(logout 接线＋idle toast);R1 final review 修 M2(kicked TTL→refresh_secs SC-002)＋M3(revoke_others loop-until-0-active 島B2);R2 CDP-1 揪出補 backend.auth.session.kicked i18n(7777 modal 譯文)。cargo test --workspace 148 綠;base-web typecheck/fork-delta-lint 綠;CDP-1~4 實機全綠(CDP 兌現 L-053/L-015 揪出 R2 raw-key bug)。憲法 v1.3.0 §I.7 島 A/B/C/D。
- 2026-07-06｜feature_close｜005-auth-login｜認證縱切收刀（波1第二功能刀）：補齊 004 授權 seam 另一半——jwt sign 升 production＋TTL 公式（access min(300,N×60÷2)/refresh N×60）＋三態 router（Public/Authed/Policy）；login（防枚舉 collapse 1000＋dummy-argon2 時序拉平＋sys_login_attempt exactly-one/best-effort/IP 最小版）＋getUserInfo（DB-fresh roles＋casbin button 枚舉＋userId 字串）＋無狀態 sliding refresh（活性 gate＋8888、sys_token 零寫 FR-016、剝離 rotation）＋dynamic route 三端點（getUserRoutes casbin menu 過濾＋祖先包含組樹、getConstantRoutes、isRouteExist）＋4 alt-login stub（2222）；m003 seed session_idle_timeout＋validation range（5..1440）；argon2 0.5.3 引 server crate；gate2 additive-seed 白名單（ADR 0032、精修 0021、凍結 fixtures byte-pure）。base-web：dynamic 切換＋常數路由合併修（★AUTH-WIRING a）＋stub typings(ADAPT)/wrapper(WRAPPER)/三表單接线(b)/captcha 接线(c)＋backend.auth.* 四鍵三語（I18N-WIRING ii/iii）＋wire-schema 重抽（+4 Api.Auth defs、byte 冪等）。cargo test --workspace lib 102＋契約 13-case bijective/entity_access_lint/wire_schema/13碼 全綠；CDP 實機 9 項（Edge@9229）全驗；SC-001~008 滿足、FR-001~017 覆蓋；活書 §5/§6 as-built 填入。
- 2026-07-05｜feature_close｜004-system-settings｜系統設定縱切收刀（波1首功能刀＋base-web 首刀）：後端首建 auth seam（enforce_mw JWT-decode＋require_policy DB-fresh roles→casbin enforce super-only→5003；JWT sign/登入延 auth 刀）＋facade/op-log（mutate_in_txn 同 txn、KV String-PK entity_id=None、setting_key 進 payload）＋型別驗證 registry（ADR 0026 per-key 範圍＋canonical 正規化＋未知型 fail-loud）＋兩端點（getSystemSettings/updateSystemSetting、SettingItem camelCase settingType、審計欄不上 wire）＋entity_access_lint 首建＋per-route 契約裁判（SettingItem vs 快照 Api.SystemManage.SystemSetting）＋demo 清償（B-056、覆蓋閘 3↔3）；前端 base-web 首刀＝ADAPT typings/WRAPPER service/★MODAL-WIRING(e) 設定頁（前綴分區＋型別驅動控件＋恆 refetch＋密碼策略固定排序＋i18n label＋info-icon tooltip）＋★I18N-WIRING(i)~(iv)（攔截器 msg→$t backend 命名空間、全 zh-TW primary locale 525 鍵繁化、三語選單簡/繁/English）；jsonwebtoken 10.4.0(rust_crypto)/metrics 0.24.6 拍板釘版；cargo test --workspace 74 綠、quickstart A~H 全綠、SC-001~007/FR-001~016/US1-3 全滿足、holistic review SHIP-READY；fork-delta 原行紀律機器化（tools/fork-delta-lint 掛 pre-commit）

## reference 對賬
- reference/routes：真表（來源＝rust-api/server/src/router.rs 的 ROUTES const、由 generate 重算）
- reference/ports：真表（來源＝compose 三檔的 ports: 段、由 generate 重算）
- reference/schema：真表（來源＝reference-src 的 schema-snapshot.json＋archetype-map.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/accounts：真表（來源＝reference-src 的 accounts-snapshot.json、由 generate 重算；快照由 refresh 自實庫撈）
- reference/screens：真表（來源＝base-web/src/router/elegant/routes.ts 的 generatedRoutes const、由 generate 重算；全巢狀 route flatten）
