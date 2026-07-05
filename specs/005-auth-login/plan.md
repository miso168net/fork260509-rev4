# Implementation Plan: 005-auth-login 認證縱切（JWT 簽發＋登入＋閒置逾時＋dynamic route）

**Branch**: `005-auth-login` | **Date**: 2026-07-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-auth-login/spec.md`；上游＝
`docs/brainstorms/005-auth-login.md`（七題拍板）、ADR 0027（授權 seam 接續契約）／0029（alt-login
stub）／0030（閒置逾時 sliding refresh）、constitution v1.1.0 §I.1/§I.2/§I.3/§I.5/§II #2/§III。
clarify 1 題已入 spec（停用帳號本刀即防禦性實作）。

## Summary

補齊 004 授權 seam 的另一半（ADR 0027）：`jwt::sign` 升 production＋登入端點（防枚舉 collapse
＋dummy-argon2 時序拉平＋登入稽核 exactly-one）＋無狀態 sliding refresh 換發端點（ADR 0030：
access TTL＝min(300s, N×60÷2)、refresh TTL＝閒置設定 N、活性 gate、驗失敗 8888）＋getUserInfo
（casbin button 枚舉）＋dynamic route 三端點（getUserRoutes casbin menu 過濾＋祖先包含組樹、
getConstantRoutes、isRouteExist）＋4 條 alt-login stub（ADR 0029、2222）＋router 三態化
（Public/Authed/Policy）。資料面 m003 seed `session_idle_timeout`（基線 m002 凍結、casbin 零新
列）。前端（base-web）：dynamic 切換＋常數路由合併修＋alt-login stub 接线＋captcha stub 接线
＋backend.auth.* i18n；**其中 route store／login 表單／captcha hook 三處 inline 逾現有授權軌道
→ 本 plan 立 Amendment（新 ★AUTH-WIRING 軌道、user 拍板）**。驗收＝cargo（容器 serial）＋
base-web 靜態閘＋**CDP 實機瀏覽器 9 項**（承 004 login-gated 走查債）。

## Technical Context

**Language/Version**: Rust（沿 001；rust-toolchain 已釘）；前端 Vue 3＋TypeScript（vue-tsc）
＋naive-ui；locale＝vue-i18n（zh-TW primary、004 已建）。

**Primary Dependencies**: 後端零新拍板依賴——jsonwebtoken 10.4.0（`sign`＋`verify`、HS256
rust_crypto、004 已引）／casbin 2.20.0（enforce、adapter 已 vendored）／metrics 0.24.6（004 已引）；
**argon2 需自 migration crate 引入 server crate**（登入 verify、版本＝比對 migration crate 現值
釘全數值、research R1）。前端零新 runtime 依賴（stub wrapper/合併修皆用既有機制）。**零 Redis**
（session/denylist 留 session 刀）。

**Storage**: baseline（casbin 149／sys_menu 78／sys_user 3 seed／sys_login_attempt 表／
system_settings 8 seed）＋**m003 新 migration**：seed `session_idle_timeout`（number、預設 60、
單位分鐘）；基線 m002 凍結不動、casbin 零新列、m003 down 對稱刪鍵。

**Testing**: 後端容器內 `cargo test --workspace` serial（login 四態＋attempt 斷言＋dummy-argon2／
refresh 換發/過期/活性 gate/設定生效／getUserInfo／getUserRoutes 過濾＋祖先包含／stubs 2222／
三態保護／契約 case＋wire-schema byte 冪等／entity_access_lint）＋命令級（quickstart）。前端
`pnpm gen-route && typecheck`＋lint＋locale 對等＋契約對齊（無 vitest、004 拍板）。**★CDP 實機
瀏覽器驗收**（`127.0.0.1:9229`、入口 front-nginx `http://localhost:42080`、9 項；L-015/L-053 紀律）。

**Target Platform**: 001 dev stack（WSL2 Docker Compose、host 零工具鏈）。

**Project Type**: web（rust-api 後端縱切＋base-web 前端）；雙倉 worktree（各兩段式 commit＋pin bump）。

**Performance Goals**: 不破 001 啟停時效；login/refresh 低頻、每次 DB-fresh 讀設定＋角色（super-only
面小）、無效能標的。

**Constraints**: rust build/test 全程容器內 serial；base-web 改動限授權軌道＋fork-delta `rev4-inline`
（＋fork-delta-lint 機器強制）；13 碼零新碼；upstream typings 凍結不動；交付碼零前代代號；
JWT sign 本刀升 production（004 為 `#[cfg(test)]`）。

**Scale/Scope**: 後端 10 端點（3 auth＋3 route＋4 stub）＋router 三態＋4 facade（sys_user/sys_menu/
sys_role/sys_login_attempt）＋jwt sign 升級＋m003；前端 dynamic 切換＋3 類 inline 接线（合併修/
表單 stub/captcha）＋WRAPPER/ADAPT 新檔＋backend.auth.* 四鍵三語；守門沿既有＋CDP 9 項。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* 對照 constitution
**v1.1.0**（本 plan 期經 ADR 0031 Amendment 至 **v1.2.0**）§IV 九題：

| # | 檢查 | 結果 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 權威／未供 endpoint？ | **No** | 本刀供 base-web 用到的 /auth/login、getUserInfo、refreshToken、/route/{getUserRoutes,getConstantRoutes,isRouteExist} 全部；能力不縮減 |
| 2 | 動 base-web inline？屬 §III.2 哪範圍？fork-delta？ | **Yes——經 ADR 0031 授權** | 授權內：`.env*`（ADAPT、§II #2 已凍結 dynamic）＋rev4-auth-stub 新檔（WRAPPER/ADAPT）＋backend.auth.* 四鍵（I18N-WIRING (ii)/(iii)）。三處逾軌 inline（route store 合併修／login 三表單 stub／captcha hook）→ **★AUTH-WIRING (a)~(c)（ADR 0031、v1.2.0）授權**；全走 rev4-inline 修改型帶 `原行:`＋fork-delta-lint |
| 3 | menu 顯示走 Casbin enforce？ | **Yes** | getUserRoutes casbin `act='menu'` 過濾（85 列已 seed 002）＋祖先包含組樹；dynamic 落地（§II #2）；demo menu 已進 seed（§I.2）；零新 seed 列 |
| 4 | wire 對齊 §I.3？ | **Yes** | upstream `Api.Auth`/`Api.Route` 凍結 typings（後端 serde 遷就）；13 碼零新碼（1000/3333/8888/5003/2222/5000）；msg=key（backend.auth.*/biz.auth.*）；userId 字串 id 型；信封 Res；無 mock（wire 權威＝base-web） |
| 5 | 前代 source 拷貝？§I.5 例外？防回歸？ | **No（受控參照）** | rev3 006/014/010 結構參照、全新寫；防回歸：refresh 剝離 rotation/sys_token/single-session（留 session 刀）、無 Redis |
| 6 | 抵觸 §II 拍板？ | **No** | §II #2 dynamic＝本刀執行凍結拍板（非改）；#1（unknown header）/#3（/api strip）不涉；.env 切換走 ADAPT（§II #2 明列）——衍生 store 接线逾軌屬 §III.2 授權面（Q2/Q7），非改 §II 本身 |
| 7 | 觸及 §III ★ 軌道？授權內？補完 vs 新能力？ | **Yes——新 ★AUTH-WIRING 軌道已授權** | I18N-WIRING (ii)/(iii) auth 鍵＝授權內純加。route store 合併修／login 表單 stub／captcha hook 三處＝現有軌道未涵蓋之新能力 → **ADR 0031 立新 ★BASE-WEB-AUTH-WIRING 軌道 (a)~(c)、constitution v1.2.0**（本刀 plan 期立、user 拍板；比照 004 ADR 0028）→ 現授權內 |
| 8 | 新建業務表？§I.6 審計欄？ | **No 新表** | m003 僅 seed 一列 system_settings（表 002 已建含審計六欄）；casbin 零新列；down 對稱刪鍵 |
| 9 | 觸及 §I.7 行為島？ | **No** | §I.7 空；本刀 refresh 無狀態、無 rotation/single-session 狀態機（留 session 刀 B-021）；brainstorm 明示不觸發 Amendment → §I.7 維持空 |

**GATE：通過**（Q2/Q7 經 **ADR 0031 Amendment（新 ★BASE-WEB-AUTH-WIRING 軌道、constitution
v1.1.0→v1.2.0）解除**；本 plan 步立、user 拍板〔2026-07-05〕、已 accepted；比照 004/ADR 0028
先例）。Complexity Tracking 記軌道擴展。

### Amendment 紀錄（★AUTH-WIRING 軌道、ADR 0031、v1.2.0、user 已拍板）

新 ★ 軌道 **BASE-WEB-AUTH-WIRING**，授權 auth 刀三處 base-web inline 接线（皆 fork-delta
`rev4-inline` 修改型帶 `原行:`、fork-delta-lint 強制）：

| 子項 | 檔 | 改動 | provenance |
|---|---|---|---|
| (a) 動態常數路由合併修 | `src/store/modules/route/index.ts` | dynamic 分支 `addConstantRoutes(data)` → `addConstantRoutes([...staticRoute.constantRoutes, ...data])`（防「No match for login」破口） | rev3 已驗證（010）；§II #2 dynamic 落地的必要接线 |
| (b) alt-login 表單 stub 接线 | `src/views/_builtin/login/modules/{code-login,register,reset-pwd}.vue` | handleSubmit 假 success → 呼叫 stub wrapper、經 backend.* i18n 顯示 | rev4-new（ADR 0029 帳實收斂拍板） |
| (c) captcha stub 接线 | `src/hooks/business/captcha.ts` | getCaptcha setTimeout 假動作 → 呼叫 sendCaptcha stub、成功才倒數 | rev4-new（ADR 0029） |

嚴格限此三點、絕不擴張；第四點 → 再 Amendment。MINOR（§V.3 新增 ★ 軌道）→ v1.2.0。

## Project Structure

### Documentation (this feature)

```text
specs/005-auth-login/
├── plan.md              # 本檔
├── research.md          # Phase 0：argon2 釘版＋rev3 剝離接地＋TTL 公式＋isRouteExist 保護層核對
├── data-model.md        # Phase 1：Claims/憑證對/登入稽核/menu 樹/session_idle_timeout 形定稿
├── quickstart.md        # Phase 1：cargo test＋命令級＋★CDP 9 項驗收腳本
├── contracts/
│   ├── auth-api.md           # 10 端點 wire＋錯誤碼＋保護層＋casbin 過濾規則
│   └── frontend-track.md     # 前端軌道歸屬（含 ★AUTH-WIRING）＋fork-delta 清單＋i18n
└── tasks.md             # Phase 2（/speckit-tasks、非本命令）
```

### Source Code (repository root)

```text
# rust-api worktree（rev4-admin-rust-api）
rust-api/server/src/
├── auth/jwt.rs                        # sign 升 production（access/refresh 對）＋TTL 公式
├── auth/enforce.rs                    # 三態：enforce_mw（Authed）＋require_policy（Policy）
├── handler/auth.rs                    # login/refreshToken/getUserInfo/4 stub
├── handler/route.rs                   # getUserRoutes/getConstantRoutes/isRouteExist
├── model/facade/{sys_user,sys_menu,sys_role,sys_login_attempt}.rs  # 新 facade（過 entity_access_lint）
├── model/password.rs                  # argon2 verify＋dummy（B-043 時序拉平）
├── router.rs                          # Protection 三態（Public/Authed/Policy）＋10 端點註冊
├── config.rs/state.rs                 # JWT secret/iss/aud 配線（sign/TTL helper 落 auth/jwt.rs、R8）
└── tests/                             # login/refresh/route/stub/三態/契約/wire-schema/entity_access_lint
rust-api/migration/src/m003_session_idle_timeout_seed.rs  # seed 一列＋down 對稱

# base-web worktree（rev4-admin-base-web）——全走 rev4-inline fork-delta
src/service/api/rev4-auth-stub.ts             # WRAPPER 新檔
src/typings/api/rev4-auth-stub.d.ts           # ADAPT 新檔
src/store/modules/route/index.ts              # ★AUTH-WIRING (a) 合併修
src/views/_builtin/login/modules/*.vue        # ★AUTH-WIRING (b) 三表單 stub
src/hooks/business/captcha.ts                  # ★AUTH-WIRING (c) captcha stub
src/locales/langs/{zh-cn,en-us,zh-tw}.ts      # I18N-WIRING (ii) backend.auth.* 四鍵
src/typings/app.d.ts                          # I18N-WIRING (iii) Schema 擴充
.env / .env.test                              # ADAPT（route mode dynamic／打點）
```

**Structure Decision**: 雙倉分工——後端住 rust-api worktree（sign 升級/端點/facade/m003）；
前端住 base-web worktree（軌道授權內＋★AUTH-WIRING〔待拍〕、兩段式 commit＋pin bump）。信封/
錯誤/授權 seam 沿 003/004；rev3 006/014/010 結構參照、全新寫。

## Complexity Tracking

| 事項 | 為何需要 | 為何未選更簡替代 |
|---|---|---|
| 新 ★AUTH-WIRING 軌道＋constitution Amendment (v1.2.0) | ADR 0029（stub 帳實收斂）＋B-058/§II #2（dynamic 落地）需三處 base-web inline、逾現有軌道 | 更簡替代＝不接线前端（stub 只後端／dynamic 不落）＝違反已 accepted 之 ADR 0029＋§II #2；三處為交付 approved 設計的最小 inline 集 |
| 無狀態 sliding refresh（access TTL 折半公式） | user 拍板閒置逾時語意（ADR 0030）；純 JWT exp 不自滑動 | 更簡＝固定長 access（失閒置保護）／server 記最後活動（提前吞 B-021 session 狀態、單副本限制） |

## 憲法 Post-Design Re-Check（Phase 1 之後）

Phase 0/1 產物（research／data-model／contracts／quickstart）復查 §IV：
- **Q2/Q7**：base-web 改動全落授權軌道——ADAPT（.env）／WRAPPER＋ADAPT（rev4-auth-stub 新檔）／
  I18N-WIRING (ii)/(iii)（backend.auth.* 四鍵）／**★AUTH-WIRING (a)~(c)（ADR 0031、v1.2.0）**；
  設定頁走 description fallback 零改動（R10）→ Amendment 面精確限三點、未外溢。**GATE 維持通過**。
- **Q4**：contracts/auth-api 全對齊 §I.3（信封／13 碼零新碼／msg=key／userId 字串／無 mock）。
- **Q5**：research R2 逐段剝離（rotation/sys_token/single-session 留 session 刀）＝結構參照、
  零整檔拷貝、防回歸帶入。
- **Q8**：m003 僅 seed 一列（表 002 已建含審計六欄）、casbin 零新列、down 對稱——無新表。
- **Q9**：§I.7 維持空（refresh 無狀態、無狀態機入憲）。

Phase 1 未引入新軌道觸碰／新業務表／前代拷貝——**GATE 維持通過**。

備註：核心 plan 的「update agent context」步驟 rev4 明示跳過（agent-context extension 未安裝、
沿 001~004 先例）；技術上下文由本 plan＋brainstorm＋research 承載。
