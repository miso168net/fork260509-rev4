# Research: 014-user-center（Phase 0）

前置：brainstorm 期五鏡頭深度探索（rev3 前端 UI／後端契約／治理設計依據／rev4 差異面／CDP 實機快照）＋彙整 critic＋3 鏡頭對抗式審查已完成大宗接地（docs/brainstorms/014-user-center.md §0）；本檔收斂 plan 期補查（SYNTH 缺口 1/2/3/7）與全部技術決策。零 NEEDS CLARIFICATION 殘留。

## R1 密碼政策 7 鍵常數同源（SYNTH 缺口 1）

- **Decision**: getPasswordPolicy 端點的 allowlist 直接復用 `model/password.rs` 既有 `KEY_*` 常數（`password_min_length`／`password_max_length`／`password_require_{lowercase,uppercase,digit,special}`／`password_forbid_username`、行 76 起）——將 7 鍵常數 pub 化（或聚合為 `pub const PASSWORD_POLICY_KEYS: [&str; 7]`），端點過濾與 `load_policy`（行 168 起、`find_by_keys` 單快照）同源。
- **Rationale**: 防兩處字面漂移（brainstorm §3.2 明載）；`load_policy`（password.rs:171 起）已是 7 鍵單語句快照讀（011 spec FR-026 範式、島 I5 政策鍵單一快照）、allowlist 同組零新語意。
- **Alternatives considered**: 端點內另寫字面陣列（rev3 形）——兩處漂移風險、棄。

## R2 ROUTES／contract case 慣例（SYNTH 缺口 2）

- **Decision**: `router.rs` ROUTES 加 4 筆 `RouteDef { method, handler, case_key, envelope_exception: false, protection: Protection::Authed }`；case_key＝`get-profile`／`update-profile`／`get-password-policy`／`change-password`（kebab、照 `reset-user-password` 形）；契約結構斷言落 `server/tests/contract.rs`（照行 1330 起 reset-user-password case 形、每端點一筆）；registry 筆數 +4。
- **Rationale**: contract.rs 對 ROUTES 覆蓋閘「缺 case 即紅」（013 R7 實證）；Authed 先例已有（router.rs:171/179/195 getUserInfo 家族）。
- **Alternatives considered**: 無（機器閘唯一路）。

## R3 violations 明細渲染管線（SYNTH 缺口 3）

- **Decision**: 後端政策違規回 `BizData("biz.user.passwordPolicy", violations)`（011 既建、handler/user.rs:280-311 範式）；前端**零改**——攔截器對 BizData 明細的渲染管線＋`backend.biz.user.passwordViolation.*` 8 鍵三語 011 已全備（join 用 `backend.common.listSeparator`）。改密卡的政策**即時 form rules** 走 rev3 buildPolicyRules 形（消費新 auth-only getPasswordPolicy），與 011 user-operate-drawer 的 best-effort hint 形（super-only 端點、user-operate-drawer.vue:100-135）不同構——各自維持。
- **Rationale**: D2 拍板（明細形）；前端管線零工作＝011 資產直接生效。
- **Alternatives considered**: rev3 單句 tooWeak——D2 已落選。

## R4 session_event／op-log 常數沿用（SYNTH 缺口 7）

- **Decision**: session_event reason 沿用既有 `SE_REASON_PASSWORD_RESET = "password_reset"`（facade/sys_user.rs:228 附近、013 前 T017 建）；event_type＝`revoked`（靜默 8888）；op-log AuditOperation reuse `ResetPassword`＋payload 白名單 `{id, user_name}`（reset_password_audit_json 沿用）。**零詞彙表變更＝零守恆測試更動**。
- **Rationale**: 自拍 3/4（operator==target 已可鑑別自助改密 vs 管理員重設）；`record_session_events` 已是 caller-txn 內範式、直接複用。
- **Alternatives considered**: 新 reason `password_change`——動詞彙守恆測試、鑑別力增益零、棄。

## R5 change_own_password 固定序（島 I1/I2/I5 合規）

- **Decision**: 鎖外＝預讀列（`sys_user::find_active_by_id`——★rev4 現無此讀端、須新建：鏡像 sys_role.rs:96 範式〔濾 deleted_at、無鎖〕）→confirm==new→verify(old, phc)（argon2、鎖外）→**new≠old 明文比對**（改密端點固有規則、非政策鍵）→load_policy＋validate_against_policy（含 user_name）→hash(new)（鎖外）。txn 內＝advisory_lock_user_db（與 login/refresh 共鎖）→find_active_by_id_for_update 重讀（查無→notFound）→**phc 純字串比對**（與鎖外 verify 所讀一致；已變→oldMismatch 誠實拒）→UPDATE password＋updated_at/by→revoke_others_of_user(txn, uid, keep=claims.sid)→逐 sid session_event(revoked, password_reset)→op-log（password redacted）→commit→broadcast_revocation 8888 best-effort。
- **Rationale**: 島 I5「密碼雜湊 MUST NOT 於持有列鎖期間計算」＋島 I2 登入款「純比對不重跑雜湊」範式（auth.rs:279 先例）＋島 I1 lock-then-redecide；對抗審查 blocker 4 的修正結論；`revoke_others_of_user` 既存（facade/sys_token.rs:143）。
- **Alternatives considered**: 鎖內 argon2 verify（brainstorm 初稿）——觸島 I5 字面、對抗審查否決。

## R6 getUserRoutes 白名單附掛點（ADR 0065）

- **Decision**: `handler/route.rs::get_user_routes`（行 48 起）於 casbin 過濾結果之後、組裝回傳前，聯集寫死常數 `SELF_SERVICE_ROUTES`（現僅 user-center 一項；含去重——既存 R_SUPER menu policy 下 super 會雙來源命中）；`resolve_home`（行 138）零改動、既有 4 筆測試（route.rs:581-611）擴充一筆「零 menu policy 角色 home 兜底落 user-center」交互案＋白名單兩向測（無政策角色得 self-service 路由／白名單外路由不受影響）。
- **Rationale**: D1 拍板＋ADR 0065；附掛點在單一 handler＝§I.2「前端仍只消費 getUserRoutes 單一來源」不變。
- **Alternatives considered**: seed 全角色 menu policy（新角色漏配即 404）／constant route（免登入層語意錯位）——brainstorm 已證僞落選。

## R7 rev3 前端承襲與不可照抄清單

- **Decision**: 承襲＝brainstorm §0.1 全清單（四卡骨架／NGrid 1 s:2／label-width 100·76 刻意差異／radio 三選切換清憑證＋type 翻轉／toRef confirm rule／buildPolicyRules 演算法／部分更新形／佔位三處＋comingSoon toast／.uc-readonly 純文字／三態後綴／直接路徑 import）。**不可照抄四處**：島 I1 鎖（後端）／島 I5 時序（後端）／user_gender 走 `wire_enum12` 字串 1|2 形（handler/user.rs:226-232 範式＋`i16_to_wire`、值域外 None 不動）／錯誤鍵 rev4 域名（biz.user.userNotFound 等）。前端行為增補三處＝D3 成功 toast 專屬鍵／D4 forbid_username 第 7 鍵即時提示／clarify 新≠舊即時提示（舊密碼驗證方式下比對 credential 欄）。
- **Rationale**: user 拍板「UI 全部要一樣」＝版面層逐項復刻；行為增補皆非版面變動（brainstorm D3/D4＋clarify 親決）。

## R8 i18n 面與 amendment 字面

- **Decision**: `page.userCenter.*` 29 鍵（rev3 30 鍵砍死鍵 changePwdBtn）×3 語＋`App.I18n.Schema` 鏡像；新鍵 3 枚入 `backend.biz.user.*`（oldPasswordMismatch／passwordMismatch／passwordSameAsOld）＋改密成功 toast 專屬鍵（page.userCenter 命名空間內）＋D2 統一單句鍵 pwdPolicyNotMet（★U4 勘誤 2026-07-17：本節原盤點漏列表單即時驗證統一單句所需鍵——rev3 tooWeak 屬 backend 域、被歸「明細管線零工作」；user 親決 A 案補於 page.userCenter 域、三語照 rev3 tooWeak 逐字）；zh-TW 在地化轉寫（儲存／信箱／手機號碼）、zh-CN 底本＝rev3 逐字、en 照 rev3 底本潤飾。Amendment 候選字面＝§III.2(g) 於「消費 auth-only 自助端點（operator＝本人）」後加「＋對應 i18n key」（照 (c)(d)(e)(h)(i) 五用途同形；MINOR v1.11.0→v1.12.0）。
- **Rationale**: 對抗審查 blocker 5＋013 v1.11.0 (d) 擴字串判例（字面縫隙以擴字串正名、不走寬讀）。
- **Alternatives considered**: 寬讀「(g) 授權頁面隱含 i18n」——五用途明寫對照下站不住、棄。

## R9 「新密碼＝舊密碼」規則落點（clarify 親決）

- **Decision**: 落 **facade 固定序**第 4 步（舊密正確之後、政策之前；handler 僅欄位反序列化與拒因映射）、`new_password == old_password` 明文比對；拒因 `biz.user.passwordSameAsOld`（2222）；前端 form rule 同步（僅舊密碼驗證方式下比對）。**MUST NOT 入 `validate_against_policy`**——單一驗證點由建帳／管理員重設共用、彼等無舊密可比，入點即分叉（spec 治理節明文）。
- **Rationale**: clarify 2026-07-17 user 親決；ADR 0054 零分叉不變式。
- **Alternatives considered**: 政策鍵化（password_forbid_same_as_old 設定）——無人要求可配置性、YAGNI 棄。

## 未決節

無——九項全定案；amendment 親決 GATE（(g) 擴字串＋ADR 0065 轉 accepted）＝治理程序非技術未決，時點照 013 判例（analyze 後、實作 i18n／getUserRoutes 單元前）。
