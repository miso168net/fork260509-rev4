# 020-email-verify-smtp 階段 0 brainstorm — 帳號 email 驗證＋SMTP 寄信基建（B-028 信箱半邊兌現）

- 日期：2026-07-31
- 方法：效仿目標＝公司現用 GitLab-ee（19.1.2-ee.0）SMTP 設定面（user 提供 config、值已去識別化）
  → 四鏡頭前置研究 workflow（wf_471a7c74：lettre 選型／mailpit dev 收信／Gmail 2026 政策／repo
  底座深讀）→ 拍板題逐題親決（9 題、含 user 中途兩次規則升級：**衛星表取代 sys_user 加欄**＋
  **created_{at,by} 成對慣例**）→ 設計分節核可 → ADR 0085/0086 draft 隨本檔同 commit。
- 存在理由：**B-028** 信箱半邊（手機/信箱真實驗證——本刀兌現「信箱真實驗證」＋系統首次獲得
  SMTP 寄信能力；phone 半邊與「驗證碼改密」不動、留 B-028 殘餘）。B-028 註記之 007 captcha
  底座複用在本刀落實為 token 範式平移。
- 下一步：本檔＋ADR 0085/0086 draft → commit 落 default（rev4-admin-root）→ user 審 → 手動起手
  `/speckit-specify`（feature branch `020-email-verify-smtp` 由 specify 建）。

---

## §0 接地盤點（偵察快照 2026-07-31、承重項已抽驗）

### 0.1 效仿目標：GitLab-ee 參考設定與逐鍵對映

```ruby
gitlab_rails['gitlab_email_from'] = 'user@my-domain.demo'
gitlab_rails['gitlab_email_display_name'] = 'GitlabDemo'
gitlab_rails['gitlab_email_reply_to'] = 'user@my-domain.demo'
gitlab_rails['gitlab_email_subject_suffix'] = 'GitlabDemo'
gitlab_rails['smtp_enable'] = true
gitlab_rails['smtp_address'] = 'smtp.gmail.com'
gitlab_rails['smtp_port'] = 587
gitlab_rails['smtp_user_name'] = 'user@my-domain.demo'
gitlab_rails['smtp_password'] = '****************'
gitlab_rails['smtp_domain'] = 'smtp.gmail.com'
gitlab_rails['smtp_authentication'] = 'login'
gitlab_rails['smtp_enable_starttls_auto'] = true
gitlab_rails['smtp_tls'] = false
gitlab_rails['smtp_openssl_verify_mode'] = 'peer'
```

| GitLab 鍵 | 我方落點（D5/D6 拍板後） |
|---|---|
| `gitlab_email_from` | `APP_MAIL_FROM`（compose plain env） |
| `gitlab_email_display_name` | `APP_MAIL_DISPLAY_NAME`（同上） |
| `gitlab_email_reply_to` | `APP_MAIL_REPLY_TO`（同上） |
| `gitlab_email_subject_suffix` | `APP_MAIL_SUBJECT_SUFFIX`（同上） |
| `smtp_enable` | 不設——寄信恆啟用（dev 指向 mailpit、prod 指向 Gmail），無停用態 |
| `smtp_address`／`smtp_port` | `APP_SMTP_HOST`／`APP_SMTP_PORT`（同上） |
| `smtp_user_name` | `APP_SMTP_USERNAME`（同上；空值語意見 §2.4） |
| `smtp_password` | SOPS secret `smtp_password`→`APP_SMTP_PASSWORD_FILE`（D6） |
| `smtp_domain`（HELO） | 不設鍵——lettre `hostname` feature 自動取本機名（需要再議） |
| `smtp_authentication`='login' | lettre 設 credentials 即預設嘗試 Plain＋Login、涵蓋 AUTH LOGIN |
| `smtp_enable_starttls_auto`＋`smtp_tls`=false | `APP_SMTP_STARTTLS`：true＝587 STARTTLS（`Tls::Required` 不可降級）；false＝明文（僅 dev 對 mailpit）；465 隱式 TLS 不支援（GitLab 此組亦然） |
| `smtp_openssl_verify_mode`='peer' | lettre rustls 憑證＋hostname 驗證預設啟用且不提供關閉——嚴格度≥peer |

### 0.2 rust-api 現況

- **零寄信能力**：Cargo 全卷無 lettre/smtp 依賴（Cargo.lock 的 `email_address` 是 jsonschema
  transitive、與寄信無關）；SMTP 僅以 ADR 0071 落選理由（「需四憑證」）存在。
- **設定機制**：`server/src/config.rs` 手寫 `env_or_file`（`{NAME}_FILE` 優先、空值/CHANGE-ME
  開頭 panic、fail-loud；`env_or_file_or_default` 供有安全預設之非機密——XDB_FILEPATH 先例）；
  `AppConfig` 現 10 欄；共享句柄落點＝`server/src/state.rs` AppState（Arc 廉價 clone）。
- **captcha 無狀態簽題底座**（`server/src/captcha/mod.rs`＋`throttle/mod.rs`）：claims
  `{nonce, user_name, exp, ans_mac}`、HS256 獨立金鑰、`ans_mac=SHA256(secret‖nonce‖答案)`
  防離線暴力、TTL 300s、redis `SET NX` 提交即消耗、驗證 leeway=0、產題零 DB。純函式＋redis
  原語、與 login 零耦合——可平移為 email 驗證碼 token 範式。
- **login 節流不可直掛**（B-102 結構原因實地核）：計數綁 `sys_login_attempt` 登入語意、precheck
  狀態機全 login 專屬字面、reset-on-success 移植他場景會反轉為破口。發碼節流最小複用面＝
  `redis::set_nx_ex` 冷卻鍵範式＋`warn_degraded` 觀測範式。
- **settings registry 現況**（ADR 0026、`server/src/validation.rs`）：只收 number 與 enum 型、
  string 型 fail-loud 拒收——本刀 D5 拍定全靜態 env 後**完全不觸及**。
- **update_profile**（`server/src/handler/user_center.rs`）：DTO 四欄全 Option 窄寫（Some 才
  Set）、advisory lock＋同 txn op-log；★後端對 userEmail 現況零格式驗證、原字串直落庫。
- **stub 家族**（ADR 0029）：`/auth/register`、`/auth/sendCaptcha`、`/auth/codeLogin`、
  `/auth/resetPwd` 恆回 2222——本刀不觸碰；email 驗證觸發場景在 user-center、非註冊流。

### 0.3 資料模型現況

- `sys_user.user_email`：可空、無唯一約束、零索引、無任何驗證態欄（m001 基線 17 欄）；唯一索引
  僅 `user_name` 一條 partial unique（`WHERE deleted_at IS NULL`）先例。
- **sys_user 從基線以來從未被加欄**（migration 全卷 grep 實證：alter_table 僅 casbin_rule 與
  archive 表）；功能態一律衛星表——m004 `sys_token`、m011 `sys_pwd_custody`（複合 PK、零 FK、
  變體 C 極簡欄集、raw SQL `IF NOT EXISTS`）為既成範式。
- migration 卷現到 m013；本刀新表＋索引＝m014。

### 0.4 base-web 現況

- `src/views/user-center/modules/email-card.vue`（rev4 新檔、零原行）：儲存鈕單欄部分更新
  `{userEmail}`＋**驗證碼三件式佔位組**（發送鈕＋輸入框＋驗證鈕、點擊一律 comingSoon toast、
  零網路）；i18n 鍵 `page.userCenter.verify.sendCode/codePlaceholder/verify` 已備。
- BACKLOG-DEFERRED B-103：email/phone 雙卡同構 ContactCard 提煉——本刀**不順路收**（D9 後
  email 卡動線與 phone 卡分岔加大、同構前提弱化，控範圍）。

### 0.5 機密與 compose 現況

- 019 SOPS+age 管線；新增 secret 全鏈（實地核對）＝`deploy/secrets.dev.enc.yaml` 條目＋
  `generate-secrets.sh`（生成邏輯＋數處名冊）＋`preflight-secrets.sh` REQUIRED（現 11）＋
  `docker-compose.yml`（頂層 secrets 定義＋service secrets 列＋`APP_*_FILE` env）＋
  `config.rs`＋`state.rs`；rust-api 內消費樣本＝`captcha_secret`（`alert_webhook_url` 屬
  grafana 專用、不進 config.rs）。
- compose 三檔無任何收信容器、無 1025 埠；dev 專用服務先例＝`docker-compose.dev.yml` override。

### 0.6 外部研究精華（wf_471a7c74、查證日 2026-07-31）

- **lettre 0.11.22**（2026-05-14、無更新 pre-release）：維護活躍（近三月三版、含 boring-tls
  hostname 驗證反轉安全修正）；MSRV 1.85（本專案 rust 1.96.1 相容）；`starttls_relay`＝587
  STARTTLS 且 `Tls::Required`；AUTH LOGIN 內建；憑證＋hostname 驗證預設啟用。替代品 mail-send
  0.6.1 活躍但 0.x 早期、生態遠小——落選。來源：crates.io/docs.rs/github lettre 官方。
- **mailpit v1.30.6**（2026-07-28）：image `axllent/mailpit`、SMTP 1025／UI+API 8025、內建
  HEALTHCHECK（`/mailpit readyz`）；REST API 可機器斷言收信（`GET /api/v1/message/latest` 取
  Text/HTML 抽碼、`GET /api/v1/search?query=to:...`、`DELETE /api/v1/messages` 清箱）；
  MailHog 2020 起停更、mailpit 為其 drop-in 主流替代。來源：mailpit.axllent.org 官方文件。
- **Gmail 2026 政策**：2025-03-14 起 SMTP basic auth（原始密碼）全面停用，**app password 明文
  保留為例外、無淘汰時程**（前提＝帳號啟 2SV、Workspace 管理員未封鎖）；smtp.gmail.com 587
  路徑上限 2000 封/日（超限暫停最長 24h）；**From 須為登入帳號或其已驗證 send-as alias、否則
  被改寫回登入帳號**；帳號改密碼會撤銷全部 app password；量大備選＝smtp-relay.gmail.com（IP
  allowlist、10000 收件人/日）。SPF include `_spf.google.com`＋Admin console 開 DKIM。
  來源：support.google.com／knowledge.workspace.google.com 官方文件。

---

## §1 拍板記錄（user 親決 9 題、2026-07-31）

- **D1 驗證流形＝六位驗證碼回填**。信件內容＝短效六位數字碼、user 回填完成驗證。落選：點擊
  連結（需對外 base URL 設定、dev/內網不可達、企業信箱掃描器誤觸需確認頁、現成 UI 要改）；
  兩者並行（攻擊面與工作量近倍、違最小可行）。
- **D2 email 唯一性＝partial unique**。`lower(user_email)`、`WHERE deleted_at IS NULL AND
  user_email IS NOT NULL`——未填不受限、軟刪不佔用、大小寫視為同一。落選：不加（SSO email
  對映前提缺失、延後再付一次）；full unique 含軟刪（email 永久佔用、與 user_name 先例不一致）。
- **D3 存驗順序＝驗證即提交**。新 email 驗過碼才寫入庫、庫不動直到成功；無 pending 欄、驗證中
  狀態活在無狀態 token。決定性論證：D2 之下「先存後驗」讓未驗證值也佔唯一額度＝任何人可先把
  別人信箱存進自己帳號佔位、擋住真擁有者綁定；驗證即提交結構性消滅佔位攻擊面。副作用：email
  卡獨立儲存鈕退場。
- **D4 admin 端語意＝admin 填寫恆未驗證**。驗證語意＝擁有者本人證明控制權、admin 代填證明不了；
  SSO 對映防 admin 手滑放錯人進門。落選：視同已驗證；可勾選標記（例外通道使 verified 欄不可
  單純信任）。
- **D5 非機密設定＝全 compose plain env**（八鍵見 §0.1 對映表）。仿 GitLab 全靜態；零 DB 改動、
  零 settings registry 擴充（string 型 validator 是獨立刀）。落選：settings 管理頁可調；混合。
- **D6 機密切法＝僅 `smtp_password` 一支入 SOPS**。user_name 本質是 email 地址非真機密、走
  plain env（GitLab 同款明文 config）。落選：smtp_url 單條（非機密捲進密文、換 host 也要 SOPS
  儀式、密碼特殊字元需 URL encode）；user+password 兩支（多一支儀式、收益無）。
- **D7 寄信 crate＝lettre 0.11.22 釘版**。雙查完畢（rev3 無寄信先例＝全新能力；官方最新 stable
  即此）。落選：mail-send 0.6.1（§0.6）。
- **D8 dev 驗收＝mailpit v1.30.6 入 `docker-compose.dev.yml`**。真 SMTP 鏈路端對端機器驗收
  （API 撈信抽碼）而非只靠 mock。落選：腳本式 SMTP sink（自寫協定處理工程量反而大）；純 mock
  （整條投遞鏈零機器驗收、風險後置 prod）。
- **D9 驗證態落點＝衛星表 `sys_user_email_verify` 存「已驗證值」**（user 主動升級、取代原
  sys_user 加欄案）。已驗證＝比對導出（`lower(sys_user.user_email)=lower(verified_email)`）、
  不存狀態欄；admin 改 email 後衛星列自然不匹配→自動未驗證——**admin 寫入路徑零改動、未來
  任何新寫入路徑（SSO JIT、匯入）也不可能忘記清除（結構保證、非程序紀律）**。欄集經 user 二次
  校正納入 created_{at,by} 成對慣例。落選：sys_user 加欄（打破「sys_user 從未加欄、功能態走
  衛星表」範式、動共用 entity、清除語意靠每條寫入路徑自律）；鏡像現值＋狀態欄（同一事實兩個家、
  漏同步即靜默假態）。語意註記：admin 把 email 改回曾驗過的舊值→已驗證自動恢復（擁有權證明
  事件確實發生過、op-log 有時間軌；與 GitLab confirmed 語意一致）。

---

## §2 設計全案

### 2.1 資料模型（m014）

```sql
CREATE TABLE IF NOT EXISTS sys_user_email_verify (
    user_id        bigint      NOT NULL,   -- 標的使用者；單一 PK（1:1）
    verified_email varchar     NOT NULL,   -- 最後驗過的值、原樣保存；比對時 lower()；型別對齊 sys_user.user_email 現型（spec 逐字定稿）
    verified_at    timestamptz NOT NULL,   -- 最後一次完成驗證時刻（upsert 刷新）
    created_at     timestamptz NOT NULL,   -- 列首建時刻＝該 user 首次完成信箱驗證（upsert 不動）
    created_by     bigint      NOT NULL,   -- 列首建操作者（upsert 不動；本刀恆＝本人，SSO/匯入時代有鑑別價值）
    CONSTRAINT pk_sys_user_email_verify PRIMARY KEY (user_id)
);
```

- 表性質：零 FK（ADR 0009 對齊）、硬刪、無 updated_*/deleted_*（m011 變體 C 同形）、raw SQL
  `execute_unprepared`＋`IF NOT EXISTS` 冪等；寫入形＝`ON CONFLICT (user_id) DO UPDATE SET
  verified_email=EXCLUDED.verified_email, verified_at=EXCLUDED.verified_at`。
- 同 m014：sys_user 純索引（零欄位改動、entity 不動）——
  `CREATE UNIQUE INDEX IF NOT EXISTS sys_user_user_email_active_uniq ON sys_user
  (lower(user_email)) WHERE deleted_at IS NULL AND user_email IS NOT NULL`；up 遇既有重複資料
  fail-loud 中止（migration 前先掃 dev 庫、見 §4）。down 對稱：drop index＋drop table。
- 新 entity `entity/src/sys_user_email_verify.rs`；已驗證判定收 facade 單一純函式（比對導出）。

### 2.2 驗證碼 token 與端點（007 範式平移）

兩支新端點（`Protection::Authed`、`/userCenter/` 家族；router 三源 lint＋wire 契約照走）：

1. **sendEmailCode** `{newEmail}`：後端格式驗證（本刀新增、現況零驗證）→ 唯一性預檢
  （fail-fast、誠實回「此 email 已被使用」——防枚舉 collapse 口徑僅屬 login 家族、組織內部
  後台不延伸）→ 節流（§2.6）→ 產六位數字碼 → 寄信（§2.4）→ 回無狀態簽章 token。claims＝
  `{nonce, uid, new_email, exp, code_mac}`：nonce 隨機 16 bytes hex；uid 綁定操作者；exp＝
  簽發＋**600s（TTL 10 分鐘）**；`code_mac=SHA256(secret‖nonce‖碼)` 防離線暴力；HS256 簽以
  獨立金鑰 `email_verify_secret`（金鑰隔離先例）。庫零寫入。
2. **verifyEmailCode** `{token, code}`：驗簽/exp/uid 綁定 → 嘗試計數 redis `INCR`＋`EXPIRE`
  （**上限 3 次**/nonce、超限即廢）→ code_mac 比對 → 成功即 redis `SET NX` 消耗 nonce＋
  advisory lock 下同 txn：更新 `sys_user.user_email`＋衛星表 upsert＋op-log（before/after
  白名單快照、操作者本人）→ 回刷新後 profile 投影。

與 captcha 範式的兩處刻意偏差（工程自拍）：**容 3 次嘗試**（email 往返成本高、打錯一字即廢太
傷 UX；3/10⁶ 猜中面可忽略）；**成功才消耗**（captcha 是提交即消耗）。

### 2.3 寫入路徑收斂

- **updateProfile DTO 移除 `userEmail`（四欄→三欄）**：驗證即提交後自助端寫 email 唯一路徑＝
  verifyEmailCode，不移除即存在繞過驗證的直寫後門。wire 契約與前端型別同步改。
- admin addUser/updateUser **程式碼零改動**（D9 結構保證）。
- profile GET 投影加 `emailVerifiedAt`（衛星 JOIN 導出、NULL＝未驗證）；下一刀 SSO 的「以已
  驗證 email 找帳號」＝同款 JOIN 比對。

### 2.4 寄信基建（rust-api 新模組 `server/src/mailer/`）

- lettre 0.11.22、`default-features = false`、features＝`builder, hostname, smtp-transport,
  pool, tokio1, tokio1-rustls-tls`；`AsyncSmtpTransport<Tokio1Executor>` 句柄掛 AppState。
- 設定鍵（全 `env_or_file` 範式）：見 §0.1 對映表。`APP_SMTP_USERNAME` 走
  `env_or_file_or_default` 空預設——**空＝跳過 AUTH（dev 對 mailpit）、非空＝AUTH LOGIN**；
  `smtp_password` 恆讀（fail-loud 一致性）、dev 為亂數 leaf 未消費。
- `APP_SMTP_STARTTLS`：true→`starttls_relay`（`Tls::Required`、憑證驗證預設開＝等效 peer）；
  false→明文 builder（僅 dev）。465 隱式 TLS 不支援。
- 執行模型：handler 內同步 await＋**timeout 15s**；失敗回明確錯誤碼（如
  `biz.userCenter.emailSendFailed`）；**不建 queue、不重試**（首刀最小形；未來消費場景增多再
  議非同步化）。
- 信件：純文字、六位碼＋有效期說明、主旨帶 `APP_MAIL_SUBJECT_SUFFIX`、zh-TW 文案（spec 定稿）。

### 2.5 機密（SOPS 新增 2 key、儀式全鏈見 §0.5）

- `smtp_password`：**亂數 leaf 生成**（dev 對 mailpit 不消費、無害；不用 CHANGE-ME 佔位——
  config.rs 對 CHANGE-ME 開頭 panic、會炸 dev boot）；prod 真值（Gmail app password）填法入
  RUNBOOK（沿 §15.4 回寫加密檔流程）；prod 密文分層本身仍屬 B-115 遞延範疇。
- `email_verify_secret`：亂數 leaf 自動生成（同 jwt_secret 形）。
- preflight REQUIRED 11→13；RUNBOOK 新節：Gmail 運維約束（2SV＋app password 建立步驟、
  **From＝登入帳號或已驗證 alias** 硬約束、2000 封/日配額、改帳號密碼撤銷 app password、
  量大改 smtp-relay 備選）。

### 2.6 節流（常數寫死程式碼、沿 CAPTCHA_TTL_SECS 先例；不入 system_settings）

- 重發冷卻：redis `SET NX EX` **60s**／per-user；每日上限 **10 次**／per-user（`INCR`＋
  `EXPIRE` 86400、護 Gmail 配額）。
- redis 不可用→發碼 **fail-closed**（拒發、明確錯誤；寄信非登入類關鍵路徑、安全從嚴）；觀測
  沿 `warn_degraded` 範式。不掛 login throttle 狀態機（§0.2 結構原因）。

### 2.7 前端（base-web、皆我方新檔或新增型）

- `email-card.vue` 改造：獨立儲存鈕退場→「輸入新信箱→發送驗證碼（冷卻倒數）→回填→驗證→
  成功刷新＋已驗證徽章（含 verified 時間）」；`emailVerifiedAt` 投影消費。
- service wrapper／typings 新欄照既有 declaration merging 範式；i18n 鍵 zh-TW/en 補齊。
- B-103 不順路收（§0.4）；phone-card 佔位不動。

### 2.8 dev／測試與驗收

- mailpit v1.30.6 入 `docker-compose.dev.yml`（1025 內網、`127.0.0.1:8025` UI+API、內建
  healthcheck）；dev rust-api env：`APP_SMTP_HOST=mailpit`、`APP_SMTP_STARTTLS=false`、
  `APP_SMTP_USERNAME` 空；prod 零痕跡。ports reference 由收刀 generate 自動重算。
- 測試矩陣：單元（token 產驗／MAC／TTL／次數上限／消耗）＋容器內 serial 整合（發碼→mailpit
  API 撈信抽碼→verify→DB 斷言 email＋衛星列；唯一衝突；節流冷卻與日上限；updateProfile 無
  userEmail 欄契約；admin 改 email 後 verified 導出翻假）。
- SC 草案：①E2E 真 SMTP 鏈路機器驗收（信寄達且碼可驗）②錯 3 次即廢、冷卻與日上限生效
  ③admin 改 email 即呈未驗證、改回舊值自動恢復④唯一索引擋重複（大小寫變體亦擋）⑤update
  profile 直寫 email 路徑不存在（契約級斷言）。

### 2.9 治理手續（spec/plan 階段逐項落實、015 先例鏈）

- 新表：data-model §1 DDL 逐字歸屬＋`archetype-map.json` 登記＋schema-gate
  STRUCT_ADDITIVE_ALLOWLIST（表級）＋**audit_table 變體 C 表名硬編碼分支擴 sys_user_email_verify
  ＋TestAuditTable 案例同步**（015 實證：不擴必紅）＋憲法 §I.6 變體 C 先例覆蓋預期（m011 同形、
  免修憲；specify 時復核）。
- 新索引：schema-gate 儀式同刀；migration 短編號 m014、up/down 對稱。
- 新端點×2：單檔 router 三源 lint＋wire 契約重擷取；SEED allowlist 零觸及（本刀零 settings 鍵）。
- secrets：P5.1 消費者清單全鏈同刀；三層洩漏掃描防線照常（value-guard 對新 key 生效）。
- base-web：fork-delta lint 照跑（本刀預期全新增型、零原行標記）。

---

## §3 非目標（首刀明確不做）

- B-028 另半：phone 真實驗證、驗證碼改密。
- 其他寄信消費場景：密碼重設信（resetPwd stub 續留）、告警信 email 通道（ADR 0071 webhook
  不動）——mailer API 形狀留擴充餘地即可、不預建。
- 自助註冊流；多 email／secondary email；admin 使用者列表加驗證態欄（僅 user-center 呈現）；
  寄信 queue／重試／退信處理；smtp-relay.gmail.com 路徑（記載為量大備選、不實作）。
- B-103 ContactCard 同構提煉（維持 deferred）。

## §4 specify／clarify 留題

1. 衛星表名與 `verified_email` 型別逐字對齊 `sys_user.user_email` 現型（data-model 定稿）。
2. dev 庫既有 `lower(user_email)` 重複掃描（migration up 前置確認；含 seed 三帳號現值）。
3. 信件文案與主旨格式定稿（subject_suffix 位置、有效期措辭、zh-TW）。
4. 發碼端點是否需 captcha 前置（初判不用：Authed 已登入＋節流足；clarify 確認）。
5. op-log payload 白名單欄位定稿（email before/after＋verified 變化）。
6. 冷卻倒數前端狀態細節（重整後倒數重建策略）。
7. E2E 測試自容器內存取 mailpit API 的網路路徑（rev4_net 服務名直達 vs host 埠）。
8. HELO domain 是否需顯式鍵（lettre hostname 預設先行、Gmail 實測後定）。

## §5 簿記預告（收刀時執行）

- BACKLOG：B-028 改寫剩餘半邊（phone＋驗證碼改密）；B-103 維持 deferred 不動。
- events append feature_close＋NOTES 下一步＋docs-sync generate（含 ports/routes/screens
  reference 重算）。
- ADR 0085/0086 draft→accepted（隨收刀）。
