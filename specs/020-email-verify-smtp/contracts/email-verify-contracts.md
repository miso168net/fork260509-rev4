# Contracts: 020-email-verify-smtp

**4 新端點**（registry +4、每條 contract coverage case）、零新錯誤碼（拒因全 2222＋msg=i18n key）、
零新 casbin seed（皆 `Protection::Authed`）。契約面變更＝新端點×4＋updateProfile DTO 移欄＋
getProfile additive 加欄＋admin 拒因×2＋i18n 鍵＋compose/secrets 面。

## C1 GET /userCenter/emailCaptcha（新、Authed）

- 回應：`{data:{captchaId: string, captchaImg: string}, code:"0000"}`（**與 loginCaptcha 實碼同
  欄名**——captchaId／captchaImg；challenge ctx＝`email`、subject＝uid 十進位字串、TTL 300s、
  captcha_secret 簽發；claims additive 加 ctx 欄、login 端同步帶 `login`）。
- 契約 case：形狀斷言＋Authed 保護碼。

## C2 POST /userCenter/sendEmailCode（新、Authed）

- 請求：`{newEmail: string, captchaId: string, captchaAnswer: string}`。
- 成功：`{data:{verifyToken: string}, code:"0000"}`（憑據 TTL 600s；**回應不含驗證碼**）。
- 拒因（全 2222、msg 如下；序＝data-model §3）：
  - `biz.userCenter.emailCaptchaInvalid`（captcha 缺／錯／過期／重放；零寄信、不計額度）
  - `biz.userCenter.emailFormatInvalid`／`biz.userCenter.emailTaken`
  - `biz.userCenter.emailCooldown`＋`data:{remainingSeconds}`（015 C3 攜參 2222 先例同型）
  - `biz.userCenter.emailDailyLimit`
  - `biz.userCenter.emailSendFailed`（寄送逾時／SMTP 故障；不計額度）
  - `biz.userCenter.emailThrottleUnavailable`（redis 不可用 fail-closed）
- 契約 case：req/resp 形狀＋保護碼；行為斷言歸整合測試。

## C3 POST /userCenter/verifyEmailCode（新、Authed）

- 請求：`{verifyToken: string, code: string}`。
- 成功：`{data:null, code:"0000"}`（前端隨後重拉 getProfile 刷新——沿 email-card `saved` 事件形）。
- 拒因（全 2222）：`biz.userCenter.emailTokenInvalid`（簽章壞／uid 不符／已消耗／並發雙提交）／
  `biz.userCenter.emailCodeExpired`／`biz.userCenter.emailCodeAttemptsExceeded`（>3）／
  `biz.userCenter.emailCodeInvalid`（碼錯）／`biz.userCenter.emailTaken`（鎖內終判）／
  `biz.user.userNotFound`（標的失活）／`biz.userCenter.emailThrottleUnavailable`（fail-closed）。

## C4 POST /userCenter/unbindEmail（新、Authed）

- 請求：無 body。成功：`{data:null, code:"0000"}`。
- 拒因：`biz.userCenter.emailNotBound`（未綁定）／`biz.user.userNotFound`。

## C5 updateProfile DTO 變更（既有端點）

- `UpdateProfileReq` 移 `userEmail`（四→三欄：nickName／userGender／userPhone）；serde 預設忽略
  多餘欄（舊 client 送入被忽略、明文接受——同刀前端已改）。
- 契約 case：**斷言 DTO 無 `userEmail` 欄**（SC-004 契約級背書）；既有三欄行為零改動。
- 前端：`rev4-user-center.d.ts`（我方 ADAPT 檔）同步刪欄；`fetchUpdateProfile` 型別收斂。

## C6 getProfile 回應 additive 加欄（既有端點）

- `ProfileRes` 加 `emailVerifiedAt: string | null`（ISO 時刻、null＝未驗證；導出＝data-model §2
  seam）。前端 typing 同檔加欄（我方檔、直接編修）。
- 契約 case：正負向（衛星匹配→時刻／失配或無列→null）。

## C7 admin 端拒因（既有 addUser／updateUser）

- `biz.user.emailFormatInvalid`（格式守門、無值未變豁免）／`biz.user.emailTaken`（預檢或索引
  兜底映射；**非** 5000 內部錯誤）。
- 契約面：既有端點 req 形不變（欄仍在）；行為斷言歸整合測試。

## C8 i18n 新鍵（三語 zh-TW/zh-CN/en-US＋App.I18n.Schema 鏡像）

- `backend.*` 拒因鍵（**逐鍵名冊、共 12＋2**——對抗式驗證校正、不寫計數式）：
  `backend.biz.userCenter.` 之下 12 鍵＝emailCaptchaInvalid／emailFormatInvalid／emailTaken／
  emailCooldown（攜 `{remainingSeconds}` 佔位）／emailDailyLimit／emailSendFailed／
  emailThrottleUnavailable／emailTokenInvalid／emailCodeExpired／emailCodeAttemptsExceeded／
  emailCodeInvalid／emailNotBound；`backend.biz.user.` 之下 2 鍵＝emailFormatInvalid／emailTaken。
- 既有佔位鍵處置（★拍定、防四檔漂移——analyze U1）：`page.userCenter.verify.comingSoon`
  **刪**（接真後零消費；三語 langs＋Schema 鏡像四檔同步）；`phoneCode` 屬 B-028 另半、留。
- `page.userCenter.*` UI 鍵：既有 `verify.sendCode/codePlaceholder/verify` 沿用＋新增＝已驗證
  徽章（含時刻格式）／未驗證標示／解除綁定鈕與確認文案／captcha 輸入佔位／冷卻倒數格式
  （`{seconds}` 佔位）／發送成功提示／驗證成功提示。
- 信件文案＝zh-TW 固定字串（後端組裝、非 i18n 系統轄——內部後台單語信件、tasks 期定稿）。

## C9 compose／secrets 契約

- env 鍵表＝data-model §5（**6 常設 plain＋2 按需 plain**〔username／subject_suffix：不設鍵＝
  空語意、設鍵即必非空——env_or_file 空值 panic 機器強制、base 不設〕＋2 `_FILE`）；dev override
  **覆寫七鍵**＋mailpit 服務（`axllent/mailpit:v1.30.6`、1025 內網、`127.0.0.1:8025`、healthcheck
  `/mailpit readyz`）。
- SOPS +2 key（`smtp_password`／`email_verify_secret`、皆亂數 leaf）；preflight REQUIRED 11→13；
  prod compose 零 mailpit 痕跡（SC-008）。
- ports reference：mailpit 8025 由收刀 `docs-sync.py generate` 自動重算入表。

## C10 前端 email-card 動線契約（我方新檔改造）

- 狀態機：`閒置（顯現值＋驗證態徽章＋解綁鈕）→ 輸入新信箱＋captcha → 發送中 → 回填態（碼輸入
  ＋冷卻倒數＋重發鈕）→ 驗證中 → 成功（重拉 profile）`；錯誤各態回明確提示（backend.* 譯文）。
- 冷卻倒數＝純前端 60s；重整消失、誤按由 `emailCooldown` 拒因之 `remainingSeconds` 重建（clarify Q4）。
- captcha 圖點擊換題＋答錯自動重取（沿 pwd-login 既有互動慣例、但實作獨立於 login 軌道）。
- 獨立儲存鈕退場（D3 副作用）；未綁定時解綁鈕不顯示。
