# Contracts: user-center 端點家族（014、Phase 1）

4 端點全新建、**rev4 首個 auth-only 業務端點家族**。共通：`Protection::Authed`（enforce_mw 注 Claims、無 require_policy、**零 casbin seed**）；operator＝claims.uid（不信 body id）；envelope `{data, code, msg}` 凍結形；拒因 code 全 **2222**、msg=i18n key；access_log_mw／ip_gate 自動覆蓋（不讀 body——密碼零入日誌）。

## #1 GET /userCenter/getProfile

- **case_key**: `get-profile`｜**回**: `Res<ProfileRes>`（欄形＝data-model §3.1；零密碼零會話識別）
- 標的＝claims.uid；活性列查無→**Internal 5000**（比照 getUserInfo 分工）。
- createdByType/updatedByType＝classify_operator 三態折疊、不回 operator uid。

## #2 POST /userCenter/updateProfile

- **case_key**: `update-profile`｜**req**: `{ nickName?, userGender?, userPhone?, userEmail? }`（全 Option；DTO 無身分欄）｜**回**: `Res<null>`
- 部分更新：Some 才 Set、未帶 Unchanged；全 None→提前 no-op（零時戳 bump）；userGender 值域外→None 不動（wire_enum12）。
- 島 I1：txn 起手 advisory_lock_user_db＋鎖內重讀（查無→`biz.user.userNotFound`）；同 txn op-log。
- 格式驗證＝前端寬鬆（與管理面同水位）；清欄回 NULL 不做（空字串存 ''）。

## #3 GET /userCenter/getPasswordPolicy

- **case_key**: `get-password-policy`｜**回**: `Res<Vec<{settingKey, settingValue}>>`
- 7 鍵 `password_*` allowlist 投影（與 load_policy 同源常數、R1）；其他設定鍵結構性不可達。
- 任一登入者可讀（改密表單動態規則資料源；解 rev3 U2 之 super-only 403 教訓）。

## #4 POST /userCenter/changePassword

- **case_key**: `change-password`｜**req**: `{ oldPassword, newPassword, confirmPassword }`（三欄必填、Debug 遮蔽）｜**回**: `Res<null>`
- 固定驗證序＋撤 session＝data-model §4（島 I1/I2/I5 合規；keep-sid=claims.sid；廣播 8888 best-effort）。
- 拒因序：userNotFound→passwordMismatch→oldPasswordMismatch→passwordSameAsOld→passwordPolicy(violations)；鎖內：userNotFound／oldPasswordMismatch。
- ★「新≠舊」＝端點固有規則（明文比對）、**不入 ADR 0054 單一驗證點**。

## Registry／case 對帳

| # | method | path | case_key | protection |
|---|--------|------|----------|-----------|
| 1 | GET | /userCenter/getProfile | get-profile | Authed |
| 2 | POST | /userCenter/updateProfile | update-profile | Authed |
| 3 | GET | /userCenter/getPasswordPolicy | get-password-policy | Authed |
| 4 | POST | /userCenter/changePassword | change-password | Authed |

ROUTES registry **+4**；`server/tests/contract.rs` 各一筆結構斷言（缺 case 即紅）；wire_schema 測試隨 DTO 補（RFC3339 offset 斷言照 B-091 範式）。

## getUserRoutes 行為契約變更（既有端點、ADR 0065）

`GET /route/getUserRoutes`（既有、Authed）：回傳路由樹＝casbin 過濾結果 **∪ SELF_SERVICE_ROUTES 白名單**（現僅 user-center、去重）；resolve_home 兜底行為不變（零 menu policy 角色 home 將落 user-center＝新行為、測試明載）。registry 筆數不變、契約 case 不變（回應形不變、僅組裝語意）。

## 前端 fetcher 對帳（rev4-user-center.ts、4 支）

| fetcher | 端點 | 型 |
|---------|------|-----|
| fetchGetProfile | #1 | `request<Api.UserCenter.ProfileRes>` |
| fetchUpdateProfile | #2 | `request<null>`（data=部分欄） |
| fetchGetPasswordPolicy | #3 | `request<Api.UserCenter.PasswordPolicyItem[]>` |
| fetchChangePassword | #4 | `request<null>`（data=三欄） |

直接路徑 import request（不經 barrel、防 vite stale-export）；typings 走 `Api.UserCenter.*` declaration merging（rev4-user-center.d.ts）。

## i18n 新鍵對帳（隨 amendment 親決後落地）

- `backend.biz.user.{passwordMismatch, oldPasswordMismatch, passwordSameAsOld}` ×3 語（I18N-WIRING (ii)(iii)）。
- `page.userCenter.*` 29 鍵＋改密成功專屬 toast 鍵（含「其他裝置已登出」語意）×3 語＋App.I18n.Schema 鏡像（(g) 擴字串 amendment 射程）。
- 既有零工作：`route.user-center`／`common.userCenter`／`backend.biz.user.passwordViolation.*` 8 鍵。
