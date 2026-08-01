# Phase 0 Research: 020-email-verify-smtp

接地定案（四鏡頭前置研究 wf_471a7c74〔lettre／mailpit／Gmail 官方文件／repo 底座深讀〕＋
brainstorm 9 題親決＋clarify 4 題親決；外部查證日 2026-07-31）。

## R1 寄信 crate——lettre 0.11.22 釘版與 feature 組合

- **Decision**：`lettre = { version = "0.11.22", default-features = false, features = ["builder", "hostname", "smtp-transport", "pool", "tokio1", "tokio1-rustls-tls"] }`；transport 兩態建構——`APP_SMTP_STARTTLS=true`→`AsyncSmtpTransport::<Tokio1Executor>::starttls_relay(host)`（`Tls::Required` 不可降級、憑證＋hostname 驗證預設啟用＝等效 GitLab `openssl_verify_mode peer`）；`false`→`builder_dangerous(host)` 明文（僅 dev 對 mailpit）；`.port(port)`＋`.timeout(15s)`；credentials 僅於 username 非空時設（AUTH LOGIN 涵蓋於預設 Plain＋Login 嘗試）。
- **Rationale**：D7 親決（2026-05-14 最新 stable、無 pre-release、MSRV 1.85 相容 rust 1.96.1、近三月三版含 TLS 安全修正）；rustls 免容器 OpenSSL 相依。
- **Alternatives**：mail-send 0.6.1（0.x 早期、生態小、需搭同家 builder——落選）；native-tls（容器相依重、落選）；465 隱式 TLS（`Tls::Wrapper`——GitLab 參考組亦 false、不做）。

## R2 dev 收信——mailpit v1.30.6＋REST API 機器驗收

- **Decision**：`docker-compose.dev.yml` 新增 `mailpit` 服務（image `axllent/mailpit:v1.30.6`、SMTP 1025 內網、UI+API `127.0.0.1:8025`、內建 HEALTHCHECK `/mailpit readyz`）；E2E 斷言形＝`GET /api/v1/search?query=to:<addr>` 取最新 ID→`GET /api/v1/message/<ID>` 讀 `Text` regex 抽六位碼→回填 verify→`DELETE /api/v1/messages` 清箱（setup/teardown）；容器內測試經 `http://mailpit:8025`（rev4_net 服務名直達、免 host 埠）。
- **Rationale**：D8 親決；MailHog 2020 停更、mailpit 為 drop-in 主流；API 使「信寄達＋內含碼＋碼可驗」成為機器斷言而非 mock 自證。
- **Alternatives**：腳本式 SMTP sink（自寫協定、工程量反大）；純 mock transport（投遞鏈零驗收、風險後置 prod）——皆落選。

## R3 Gmail 路徑約束（運維面→RUNBOOK 新節）

- **Decision**：prod 走 smtp.gmail.com:587 STARTTLS＋app password（Workspace 帳號、2SV 前提）；RUNBOOK 記載五約束——①app password 需 2SV、無官方落日但標「不推薦仍支援」②配額 2000 封/日、超限暫停最長 24h ③**From MUST＝登入帳號或其已驗證 send-as alias**（否則被 Gmail 改寫）④帳號改密碼→全部 app password 撤銷（換密 SOP 含重生 app password＋SOPS 回寫）⑤量大備選＝smtp-relay.gmail.com（IP allowlist、10000 收件人/日、不實作僅記載）。SPF `include:_spf.google.com`＋Admin console DKIM。
- **Rationale**：2025-03-14 Google 停用 SMTP basic auth 後 app password 為明文保留例外（官方文件查證、來源存 brainstorm §0.6）。
- **Alternatives**：OAuth2 XOAUTH2（lettre 支援但需 token 流基建、首刀不值）；restricted 25 埠 relay（僅組織內收件人、不符）。

## R4 驗證憑據——007 簽題平移＋兩處親決偏差

- **Decision**：claims＝`{nonce(16B hex), uid, new_email, exp(簽發+600s), code_mac}`、HS256 簽以獨立金鑰 `email_verify_secret`、驗證 leeway=0；`code_mac = hex(SHA256(secret ‖ nonce ‖ code))`（secret 參與＝離線不可暴力）；六位碼＝OsRng 生成 `000000`~`999999` 零填。**偏差 1**：容 **3 次嘗試**（redis `INCR`＋首次 `EXPIRE 600`、值>3 拒）——email 往返成本高、打錯一字即廢太傷 UX（captcha 可即時換題、email 不能）。**偏差 2**：**成功才消耗**（`SET NX used:{nonce}` 於鎖內、DB 寫入前——標記先於效果沿 E4 精神；txn rollback 時憑據已耗＝fail-safe 廢票、user 重發即可）。
- **Rationale**：B-028 條目明文指認 007 底座可搬；兩偏差 spec 工程自拍明載、3/10⁶×3 猜中面可忽略。
- **Alternatives**：提交即消耗（UX 懲罰過重、落選）；DB 存 pending 碼（違 D3 驗證即提交、落選）；無限嘗試（暴力面、落選）。

## R5 發碼 captcha——複用 captcha_secret＋claims additive 語境欄（機器強制隔離）

- **Decision**：新端點 `GET /userCenter/emailCaptcha`（Authed）產題——複用 `captcha` 模組與**既有
  `captcha_secret`**，**claims additive 加語境欄 `ctx`**（值域 `"login"`／`"email"`；issue 帶
  ctx、兩端 gate 各自斷言）；email 語境 subject（實欄＝`CaptchaClaims.user_name`、純 String、
  綁定比對屬 caller 職責——欄位對映明文防誤解）＝uid 十進位字串；回應與提交欄名**沿 loginCaptcha
  實碼**＝`{captchaId, captchaImg}`／提交帶 `{captchaId, captchaAnswer}`。gate 序（sendEmailCode
  ①）＝驗簽/exp/`ctx=="email"`/subject==uid 綁定→`SET NX used:{nonce}`（提交即消耗、標記先於
  比對）→ans_mac 比對；缺／錯／過期／重放→2222 且零寄信、零額度；答錯前端自動重取新題。login
  端 issue/gate 同步帶 `"login"`（token 形 additive；上線瞬間舊題於 TTL 300s 內自然過期、無遷移
  面、login 行為零改變）。
- **Rationale**：對抗式驗證（wf_f9597e2e）推翻原「subject 形制擋死」論證——loginCaptcha 屬
  Public、對任意字串發題（僅長度 64 閘、不套 validate_user_name），任何人可簽出 uid 形 subject
  題；語境欄＝機器強制隔離、零新金鑰；`used:{nonce}` 全域單耗為第二兜底。fail 方向耦合（login
  側島 E1 fail-OPEN vs 本刀 fail-closed）以 ctx 斷言分流、ADR 0085 明記。
- **Alternatives**：第三把 captcha 金鑰（儀式成本、落選）；loginCaptcha 發題端套
  validate_user_name（改 login 行為、觸島 E2「不存在帳號同要 captcha」語意——不可）；純 subject
  形制論證（被實碼推翻、撤）。

## R6 節流形——原子先佔＋失敗回補、fail-closed

- **Decision**：**原子先佔**——`SET NX emailverify:cd:{uid} EX 60`（搶佔失敗→2222 `emailCooldown`
  ＋TTL 查餘 `remainingSeconds`〔redis 模組需補 production 級 TTL 讀取原語、tasks 明列〕）→
  `INCR emailverify:day:{uid}:{UTC 日期}`（**無條件** `EXPIRE 90000`；值 >10→`DECR` 回補＋2222
  `emailDailyLimit`）→ 唯一性預檢（命中→2222 `emailTaken`、**不回補**＝枚舉抑制、spec
  plan-session 校正）→ 寄信（失敗→**盡力回補** `DEL cd`＋`DECR day`；回補失敗＝寧誤擋不誤寄、
  fail-safe 方向）→ 簽發憑據。redis 任一 Err→發碼與提交一律 **fail-closed**（2222 明確錯誤、
  零寄信零寫庫）＋`warn_degraded` 結構化告警（label 固定小集合）。
- **Rationale**：對抗式驗證（wf_f9597e2e）推翻原 check-then-act 案——k 張預解 captcha 題（nonce
  各異、單耗擋不住）之並發突發可在任何寫入落地前整批通過只讀檢查＝k 封信全寄出、冷卻與日上限
  全繞、可對任意第三方信箱轟信、SC-003 100% 拒率不可達；先佔使並發僅一筆通過（SET NX 原子裁決）；
  唯一預檢移到先佔後＋不回補＝枚舉 oracle 收斂到額度上界。fail-closed＝寄信非登入類關鍵路徑、
  安全從嚴（與島 E fail-OPEN 方向刻意相反、劃界明文：島 E 射程＝login、本刀非其轄）。
- **Alternatives**：check-then-act＋「captcha 單耗抑制並發」論證（被推翻、撤）；per-uid advisory
  鎖序列化（發碼零庫寫、為節流引 DB 鎖過重、落選）；掛 login throttle 狀態機（B-102 結構原因、
  絕不可）。

## R7 衛星表＋唯一索引＋前置重複掃描

- **Decision**：`sys_user_email_verify`（DDL 逐字見 data-model §1）＝已驗證值衛星表、比對導出（D9）；判定收 facade 單一純函式 `is_email_verified(user_email, satellite) -> Option<DateTime>`（回 verified_at、getProfile 投影與未來 SSO 共用）。sys_user 加 `sys_user_user_email_active_uniq ON (lower(user_email)) WHERE deleted_at IS NULL AND user_email IS NOT NULL`；m014 up **前置重複掃描**——active 列 `lower(user_email)` HAVING count>1 → 有即 Err 印重複清單（指名清理後重跑）、否則 CREATE UNIQUE INDEX。
- **Rationale**：D9 親決（結構保證取代程序紀律）；sys_user 從未加欄（migration 全卷 grep 實證）＋m011 衛星先例；前置掃描使 fail-loud 帶可行動訊息而非裸索引錯誤。
- **Alternatives**：sys_user 加欄／鏡像+狀態欄（D9 落選、理由存 ADR 0085）。

## R8 設定面——compose env 九鍵＋兩特例

- **Decision**：`APP_SMTP_HOST`／`APP_SMTP_PORT`／`APP_SMTP_STARTTLS`／`APP_MAIL_FROM`／`APP_MAIL_DISPLAY_NAME`／`APP_MAIL_REPLY_TO` 走 `env_or_file` 必填 fail-loud；**兩特例＝「不設鍵即空語意」**：`APP_SMTP_USERNAME`（空＝跳過 AUTH）與 `APP_MAIL_SUBJECT_SUFFIX`（空＝主旨無後綴）走 `env_or_file_or_default` 空預設——★**base compose 不設此兩鍵**（實碼查證：`env_or_file` 對「設鍵但空值」panic 拒啟動、default 僅在鍵全缺時生效——「設鍵即必非空」為機器強制；XDB_FILEPATH 先例＝compose 全未設鍵、同形）；dev override 設 `APP_MAIL_SUBJECT_SUFFIX=[dev]`（非空合法）、不設 username；prod 部署層（B-037 刀）補 username 真值。`APP_SMTP_PASSWORD_FILE`＝必讀（fail-loud 一致、dev 為亂數 leaf 未消費）。base compose 六必填鍵載 Gmail 形預設、**dev override 覆寫七鍵**（host=mailpit、port=1025、starttls=false、from、display_name、reply_to、suffix）。HELO＝lettre `hostname` feature 自動、不設鍵（Gmail 實測有異再議——spec §4 留題結案為「先不設」）。
- **Rationale**：D5/D6 親決；settings registry 現況拒收 string 型、零觸及；「空字串覆寫」設計被對抗式驗證推翻（config.rs 空值 panic 實碼相撞）、改為不設鍵語意。
- **Alternatives**：system_settings 管理頁可調／smtp_url 單條／user+password 雙 secret（D5/D6 落選）；哨兵值語意如 `none`（醜、易誤設真值、落選）；新增允空載入函式（多一條 config 語意路徑、不設鍵語意零新碼即達、落選）。

## R9 機密鏈——SOPS +2 key（皆亂數 leaf）

- **Decision**：`smtp_password`＋`email_verify_secret` 皆走 generate-secrets 亂數 leaf 生成（**不用 CHANGE-ME 佔位**——config.rs 對 CHANGE-ME 開頭 panic、會炸 dev boot；此點與 alert_webhook_url 的 user 自填形刻意不同）；prod 真值（Gmail app password）填法＝RUNBOOK §15.4 回寫加密檔流程、隨 R3 節記載；全鏈改動＝enc.yaml＋generate 名冊＋preflight REQUIRED 11→13＋compose 三處＋config.rs＋state.rs（captcha_secret 為 rust-api 內消費樣本；alert_webhook_url 不進 config、僅 grafana）。
- **Rationale**：019 儀式實地核對過（brainstorm §0.5）；三層洩漏掃描對新 key 自動生效。
- **Alternatives**：CHANGE-ME 佔位（炸 dev、落選）。

## R10 admin 端守門——格式無豁免＋唯一雙層攔截

- **Decision**：`validate_email_format` 單一守門（trim→基本形〔單一 `@`、local/domain 非空、無空白控制字元〕→長度 ≤254）；掛三處＝sendEmailCode／addUser（沿現行 `blank_to_none` 後 Some 才驗）／updateUser（★沿現行 011 FR-007 契約、**刻意不 blank_to_none**：`None`＝該欄不動；`Some("")`＝清空、跳過守門；`Some(非空)`＝過守門——對抗式驗證校正、否則 admin 清空能力被靜默降級）；**無「值未變豁免」**（clarify Q3 user 自訂案）：存量怪值於 admin 下次觸及即被迫修正或清空、拒因指向信箱格式。唯一性＝雙層——寫端預檢（updateUser 於島 I1 鎖內 lock-then-redecide；addUser 無鎖、預檢 best-effort）＋DB 索引兜底（unique violation DbErr 映射 2222 `biz.user.emailTaken`、addUser 並發窗的權威裁決）。
- **Rationale**：clarify Q3 親決；映射兜底使 addUser 免鎖先例（島 I1 新列豁免）不被破壞。
- **Alternatives**：值未變豁免（user 否決）；本刀不加（user 否決）；admin 端僅索引裸錯（違 spec FR-006 明確拒因）。

## R11 治理路徑（R-GOV）

- **Decision**：憲法 **MINOR Amendment＝(g) 擴字串**（v1.14.0→v1.15.0）：「＋驗證 UI 佔位」→「＋信箱驗證流（發碼／回填驗證／解除綁定／其 captcha 取題）＋對應 i18n key」（1.11.0/1.12.0 擴字串判例第五度；(g) 其餘語意「登入者本人自助、auth-only 端點」不動）；同批併入 **§I.6 變體 C upsert 釋義句**（1:1 已驗證值衛星表之 upsert 刷新＝重驗事件覆寫、`verified_at` 即其時戳、不設 `updated_{at,by}`——比照 J3 對變體 B 的權威釋義形；m011 為零可變欄先例、本表為變體 C 可變欄首例、「m011 同形」單獨引法經對抗式驗證判不足）＋ **page.userCenter 鍵集敘明擴充**（(g) 之「＋對應 i18n key」自 30 鍵集擴至本刀新集合；`page.userCenter.*` 新鍵依據＝(g)＋ADR 0041 資料級釋義、**非** I18N-WIRING (ii)/(iii)——後者僅轄 `backend.*` 命名空間）。ADR 0085/0086 draft→accepted 同批；Q9 裁定零新島、「驗證即提交＋比對導出」不變式由 ADR 0085 承載不入憲（親決確認）。親決時點＝analyze 後一併、最遲於 base-web 施工與 m014 之前。
- **Rationale**：接真動作全落 (g) 語意射程（本人自助）、僅「佔位」字面過時——字面縫隙以擴字串正名、不走寬讀（013 判例）。
- **Alternatives**：寬讀「佔位含接真」（判例否決）；立新用途 (l)（射程未變、過度）。

## R12 updateProfile 欄移除——wire 影響定案

- **Decision**：`UpdateProfileReq` 四欄→三欄（移 `userEmail`）；serde 預設對多餘欄忽略＝舊 client 送 `userEmail` 被靜默忽略（**明文接受**——同刀前端已改、無真實舊 client；契約測試斷言 DTO 無該欄＝結構性堵門的機器背書）；前端 `rev4-user-center.d.ts`（我方 ADAPT 檔）同步刪欄＋`fetchUpdateProfile` 型別收斂；getProfile 回應 additive 加 `emailVerifiedAt: string | null`（ISO 時刻、null＝未驗證）。
- **Rationale**：FR-008 結構性堵直寫後門；我方 typings 檔非凍結、直接編修零 declaration merging 需求。
- **Alternatives**：後端保留欄但拒值（軟堵、可繞印象、落選）；deny_unknown_fields（全 DTO 面行為變更、超本刀範圍——B-099 既有劃界）。
