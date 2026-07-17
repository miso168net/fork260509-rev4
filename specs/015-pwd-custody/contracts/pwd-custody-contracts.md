# Contracts: 015-pwd-custody

零新端點、零新錯誤碼、零新 route（registry 筆數不變）。本刀契約面變更＝getUserInfo additive 加欄＋硬閘拒因＋settings 新鍵＋i18n 鍵。

## C1 getUserInfo 回應 additive 加欄

- 端點：`GET /auth/getUserInfo`（既有、Authed）。
- 變更：回應 `data.needChangePwd: boolean`（additive）。
  - `true`＝該登入者名下存在他人經手設密記錄（首登須換密）。
  - `false`＝純自改記錄或零記錄。
- 前端 typing：`Api.Auth.UserInfo` 加 `needChangePwd?: boolean`（net-new `rev4-pwd-custody.d.ts` declaration merging；凍結 auth.d.ts 不動）。
- 契約測試：contract.rs 補 UserInfo `needChangePwd` 正負向斷言（有他人經手→true／零列→false）；registry 筆數不變、無新 case。

## C2 硬閘拒因（middleware，非端點）

- pwd_gate_mw 判定真＋path 不在白名單→envelope `{data:null, code:2222, msg:"biz.auth.mustChangePassword"}`。
- 白名單 path（放行）：`/auth/getUserInfo`、`/route/getUserRoutes`、`/route/isRouteExist`、`/userCenter/getPasswordPolicy`、`/userCenter/getProfile`、`/userCenter/changePassword`。
- Public（結構不經閘）：`/auth/logout`、`/auth/refreshToken`。
- 掛 authed＋policy 兩子 router。

## C3 設密冷卻拒因

- 三入口（addUser 天然無冷卻／reset_password／changePassword）鎖內、既有拒因後：pair 距上次 created_at 未滿 N 秒→`{code:2222, msg:"biz.user.pwdSetTooFrequent"}`（攜剩餘秒數：BizData 帶值或前端據 created_at 推算）。
- N＝system_settings `password_change_min_interval`（缺鍵 fail-default 60、0＝停用）。

## C4 system_settings 新鍵

- key：`password_change_min_interval`、seed value `'60'`、語意＝設密冷卻秒數（0＝停用）。
- `/manage/system-settings` 頁自然可讀寫（既有 KV 頁、無需新端點；標籤 i18n 鍵 `passwordChangeMinInterval`）。

## C5 i18n 新鍵（三語＋App.I18n.Schema 鏡像）

- 產密浮層：隨機密碼（鈕文案）／產生／複製／顯示密碼／帶入。
- manage operate：「密碼」動作標籤（沿用「重設密碼」按鈕**權限碼**、但動作標籤為新鍵）。
- 強制改密頁：route 鍵＋頁標題＋說明＋成功提示＋登出鈕。
- 拒因：`backend.biz.auth.mustChangePassword`＋`backend.biz.user.pwdSetTooFrequent`（攜剩餘秒數佔位）。
- settings 標籤：`passwordChangeMinInterval`。

## C6 前端 route/元件契約

- constant route `force-change-pwd`（_builtin、blank layout、hideInMenu、constantRoutes 名單一行；免後端曝光鏈）。
- 產密浮層元件對外：`policy`（讀 getPasswordPolicy 結果）→emit `apply(password)`；本地 CSPRNG、零網路。
- guard 契約：needChangePwd 真→強制頁；axios 攔截器**不動**（無兜底）。
