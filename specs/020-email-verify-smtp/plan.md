# Implementation Plan: 020-email-verify-smtp 帳號 email 驗證＋SMTP 寄信基建（B-028 信箱半邊兌現）

**Branch**: `020-email-verify-smtp` | **Date**: 2026-07-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/020-email-verify-smtp/spec.md`

## Summary

B-028 信箱半邊兌現＋系統首次 SMTP 寄信能力。核心＝**驗證即提交**（新信箱驗過六位碼才寫入、
無 pending 態、佔位攻擊面歸零）×**已驗證值衛星表 `sys_user_email_verify`**（已驗證＝
`lower(sys_user.user_email)=lower(verified_email)` 比對導出、admin 寫入路徑之驗證態零清除義務
＝結構保證）×**sys_user 純唯一索引**（`lower(user_email)` partial、排軟刪與 NULL）。四新自助
端點（emailCaptcha 取題／sendEmailCode 發碼／verifyEmailCode 提交／unbindEmail 解綁、皆
Authed）；驗證憑據＝007 簽題平移（HS256 獨立金鑰 `email_verify_secret`、TTL 600s、3 次嘗試、
成功才消耗）；發碼前置 captcha（複用 captcha_secret、subject 以 uid 語境區隔）＋冷卻 60s＋
日上限 10＋fail-closed。寄信基建＝lettre 0.11.22（tokio1＋rustls、587 STARTTLS `Tls::Required`
／dev 明文兩態）同步寄送 timeout 15s；設定全 compose env、SOPS +2 key（smtp_password／
email_verify_secret）；dev 驗收＝mailpit v1.30.6（REST API 撈信抽碼 E2E）。admin 端＝格式守門
（單一驗證點、無值未變豁免）＋唯一衝突明確拒因。治理＝(g) 擴字串 MINOR Amendment（佔位→接真
正名）＋ADR 0085/0086 accepted＋Q8 新表工具聯動＋Q9 零新島。

## Technical Context

**Language/Version**: Rust stable 1.96.1（rust-api：axum＋sea-orm＋tokio）；TypeScript＋Vue 3（base-web：soybean-admin fork、naive-ui）

**Primary Dependencies**: **lettre 0.11.22 新依賴**（`default-features = false`、features＝`builder, hostname, smtp-transport, pool, tokio1, tokio1-rustls-tls`；D7 親決釘版）；**mailpit v1.30.6**（dev 容器 `axllent/mailpit`、非 Cargo 依賴）；其餘全既有（jsonwebtoken／sha2／argon2／sea-orm-migration／vue-i18n）

**Storage**: PostgreSQL（新表 `sys_user_email_verify`＋sys_user 純唯一索引、m014 migration、零 settings seed）＋Redis（新 key 命名空間：captcha used 沿既有＋email 驗證 attempts／used／cooldown／daily，皆 TTL 自清）

**Testing**: cargo test 容器內全程 serial＋contract/wire_schema 契約閘（**registry +4**、每條 coverage case）＋schema-gate 三子命令（audit 變體 C 分支必補）＋mailpit REST API 整合斷言＋vue-tsc typecheck＋`python3 tools/fork-delta-lint.py` 直跑＋CDP 實機場景

**Target Platform**: docker compose 自架（dev 棧 +1 mailpit 服務；prod 零痕跡）

**Project Type**: web application（rust-api＋base-web 雙 submodule worktree）

**Performance Goals**: 無特定數字目標（自助低頻操作）；發碼＝同步寄信 await、timeout 15s 上限（UI 等待可受、有 loading 態）；verify／getProfile ＝ +1 主鍵級查詢（衛星表 1:1）

**Constraints**: 4 新端點零新錯誤碼（拒因全 2222＋msg=i18n key）；零新 casbin seed（Authed 非 policy）；零 settings 新鍵（節流常數寫死、沿 CAPTCHA_TTL_SECS 先例）；衛星表零 FK（ADR 0009）；驗證碼三重不洩（log／稽核／回應）；島 I1/I2 合規（統一鎖＋lock-then-redecide；本刀寫端不涉 session 撤銷）；fork-delta 預期全新增型；三語＋Schema 鏡像；prod TLS 不可降級；dev smtp_password＝亂數 leaf

**Scale/Scope**: 1 新表＋1 唯一索引＋1 migration（m014、零 seed）＋4 新端點＋1 mailer 模組＋config **10 新欄（10→20）**＋AppState **3 新件**＋SOPS 2 新 key（preflight 11→13）＋email-card 改造（我方新檔）＋service/typings 同步＋i18n 三語新鍵（backend.* 12＋2、逐鍵名冊見 contracts C8）＋mailpit dev 服務＋工具聯動（schema-gate 表級＋index 級 allowlist＋audit 分支＋archetype-map）＋RUNBOOK Gmail 節

## Constitution Check

*GATE: 對照 constitution v1.14.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（前後端同刀交付）**。四新端點（emailCaptcha／sendEmailCode／verifyEmailCode／unbindEmail）皆為 email-card 新動線所消費；getProfile additive 加 `emailVerifiedAt`；updateProfile 移 `userEmail` 欄與前端同刀同步、無先後斷差。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、預期零上游 inline**。全部改動落我方檔：`views/user-center/modules/email-card.vue`（rev4 新檔、檔頭圈界標記既有——改造非新授權面）＋`service/api/rev4-user-center.ts`（WRAPPER 我方檔）＋`typings/api/rev4-user-center.d.ts`（ADAPT 我方檔）＋locale 三檔與 `app.d.ts`——★授權依據分流（對抗式驗證校正）：`backend.*` 拒因鍵走 I18N-WIRING (ii)/(iii)；`page.userCenter.*` UI 新鍵走 **MODAL-WIRING (g)「＋對應 i18n key」＋ADR 0041 資料級 label key 釋義**（落點＝既有 (g) 014 圈界塊；(ii) 明文「不改既有命名空間」故不轄 page.*）。上游既有行 inline＝零（若施工遇必要 inline→停手回 plan 補授權）。治理正名：(g) 授權字面「驗證 UI 佔位」→接真＝**(g) 擴字串 MINOR Amendment**（見 Q7、順帶把 page.userCenter 鍵集敘明擴至本刀新集合）。 |
| Q3 | menu 顯示走 Casbin enforce？ | **不觸發**。user-center 非 Casbin menu（(g)＋ADR 0065 self-service 路由白名單既有）；零新頁、零新 route、零新按鈕碼（自助端點 Authed、非 policy 桶）。 |
| Q4 | wire 對齊 §I.3 權威序與不變式？ | **是**。envelope／13 碼矩陣凍結不動；**4 新 route→registry +4、每條補 contract coverage case**；拒因全 **2222**＋msg=i18n key（`biz.userCenter.email*` 家族＋`biz.user.email*` 家族、零新碼；冷卻拒因 BizData 帶 `remainingSeconds`＝015 C3 攜參先例同型）；updateProfile DTO 移 `userEmail`（我方 rev4-user-center.d.ts 同步、契約斷言 DTO 無該欄；serde 預設對多餘欄忽略＝舊 client 送入被忽略、明文接受）；getProfile 回應 additive 加 `emailVerifiedAt: string \| null`（我方 typings、非凍結檔、零 declaration merging 需求）；id 序列化不涉。 |
| Q5 | 從前代 source 拷貝 code？ | **否**。rev3 零寄信（純綠地）；lettre 為全新依賴非拷貝；007 captcha／簽題為 rev4 自有 as-built 之範式平移（同 repo 內複用、非前代 source）。 |
| Q6 | 抵觸 §II 拍板？ | **否**。unknown header／dynamic route／`/api` 前綴照現制、不涉。 |
| Q7 | 觸及 §III ★ 軌道？「補完」還是「新能力」？ | **是＝(g) 擴字串（MINOR Amendment）**。MODAL-WIRING (g) 字面「…＋改密碼＋**驗證 UI 佔位**…」——本刀把佔位接真（發碼／回填／解綁／captcha 取題、皆本人自助消費 auth-only 端點＝(g) 語意射程內），依 1.11.0/1.12.0「字面縫隙以擴字串正名、不走寬讀」判例（第五度）**擴字串**：「驗證 UI 佔位」→「信箱驗證流（發碼／回填驗證／解除綁定／其 captcha 取題）＋對應 i18n key」。I18N-WIRING (ii)/(iii)（backend.* 新鍵＋Schema 鏡像）＝既授權範圍內、非新用途。無其他軌道觸及；不動攔截器控制流。 |
| Q8 | 新建業務表（create migration）？§I.6 六審計欄？ | **是＝變體 C 新表＋sys_user 純索引**。`sys_user_email_verify`＝單一 PK `user_id`＋`verified_email`＋`verified_at`＋`created_at`/`created_by`（成對、upsert 不動）；零 FK（ADR 0009）、硬刪、無 `updated_*`/`deleted_*`（m011 同形、歸屬變體 C）。sys_user 加 partial unique index＝**純索引、零欄位改動**——§I.6 無 retrofit 條款標的僅審計欄、不觸；且 partial-uniq `WHERE deleted_at IS NULL` 正是 §I.6 變體 A 慣例形之延伸（user_name 先例）。★變體 C 歸類論證補強（對抗式驗證校正）：m011 為零可變資料欄先例、本表 upsert 刷新 verified_email/verified_at 為變體 C **可變欄首例**——「1:1 已驗證值衛星表之 upsert 刷新＝重驗事件覆寫、verified_at 即其時戳、不設 updated_{at,by}」隨 (g) 擴字串 Amendment 併入 **§I.6 權威釋義句**親決（比照 J3 對變體 B 釋義形；「m011 同形」單獨引法不足）。**工具聯動（m014 同 commit、缺一即紅）**：archetype-map.json 登記＋002 data-model §1 歸屬補列＋schema-gate STRUCT_ADDITIVE_ALLOWLIST（表級＋★**index 級 `(index, sys_user, sys_user_user_email_active_uniq)`**——表級項不涵蓋既有表新索引、漏登 gate1 必紅）＋**audit_table 加 `sys_user_email_verify` 變體 C 專屬分支**＋TestAuditTable 案例＋self-test 精確集合 dict 同步（含 index 項）；SEED allowlist 零觸及（零 settings 鍵）。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是＝消費島 I、零新島**。**島 I1**：verifyEmailCode／unbindEmail 皆以既有使用者為標的之寫端→交易起手 `advisory_lock_user_db(self)`＋鎖內重驗（標的活性＋唯一性終判、lock-then-redecide）；發碼零庫寫、不取鎖。**島 I2**：信箱變更／解綁**不屬**撤銷連動標的（停用／刪除／改密才撤 session）——本刀寫端零 session 操作、明文劃界。**島 I5**：不涉密碼；對偶紀律＝驗證碼三重不洩（FR-015）。**島 E**：E4 語意零反轉——自助 captcha 為另一語境消費 captcha 模組（「提交即消耗／綁定／不可還原」照搬但作用於自助端點、非 login 判定序）；實作面＝captcha claims **additive 加 `ctx` 語境欄**、login／email 兩端 issue 與 gate 各自斷言（機器強制語境隔離、零新金鑰；login 端帶 "login"＝token 形 additive、舊題 TTL 300s 內自然過期、login 行為與判定序零改動）。**新島判定＝否**（無多步狀態機：驗證中狀態活在無狀態憑據＋redis TTL、庫面單表 upsert）；「驗證即提交＋比對導出」不變式由 **ADR 0085 承載**（親決確認、不入憲）。 |

**Gate 結論**：**通過**。需 **user 親決**（治理正名、非違規）＝①**憲法 MINOR Amendment：(g) 擴字串**（v1.14.0→v1.15.0；「驗證 UI 佔位」→信箱驗證流枚舉＋page.userCenter 鍵集敘明；**同批併入 §I.6 變體 C upsert 釋義句**）②**ADR 0085/0086 draft→accepted**。親決時點照 013/014/015 判例＝analyze 後一併、最遲於 base-web 施工單元與 m014 migration 單元之前；程序照 §V.2。

**Phase 1 後複查（research/data-model/contracts/quickstart 產出＋3 鏡頭對抗式驗證 wf_f9597e2e 12 blocker 全處置後）**：九題判定**全維持**——設計產物未引入新錯誤碼／新獨立行為島／上游 inline；Q4 之 4 新端點 wire 形（captcha 欄名對齊 loginCaptcha 實碼）＋DTO 變更＋投影加欄已定稿於 contracts/ C1~C6；Q8 之 DDL＋前置重複掃描＋工具聯動（含 index 級 allowlist）已落 data-model §1；Q9 之島 I1 固定序（`find_active_by_id_for_update` 鎖內重驗＋消耗標記先於效果）與島 E ctx 欄劃界已落 data-model §3/§4；Q7 之 (g) 擴字串＋§I.6 釋義字面已定（research R11）。對抗式驗證另修：節流原子先佔（穿透面消滅）、updateUser 清空契約對齊、config 欄數統一 10→20。

## Project Structure

### Documentation (this feature)

```text
specs/020-email-verify-smtp/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R12：lettre/mailpit/Gmail 定案、token 範式偏差、captcha 語境、節流形、衛星表、設定面、機密鏈、admin 守門、治理、DTO 變更）
├── data-model.md        # Phase 1（DDL 逐字＋唯一索引＋前置重複掃描＋工具聯動＋三端點狀態機＋redis key 表＋config/env 對映＋投影）
├── quickstart.md        # Phase 1（全量閘＋mailpit E2E＋CDP 場景＋負向自證）
├── contracts/
│   └── email-verify-contracts.md   # Phase 1（4 新端點 wire＋DTO 變更＋投影＋admin 拒因＋i18n 鍵＋compose/secrets 契約）
├── checklists/requirements.md      # specify 產（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產、非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 build/test、全程 serial）
├── Cargo.toml（workspace）＋server/Cargo.toml            # 動：lettre 0.11.22 釘版（feature 組合見 research R1）
├── migration/src/m014_email_verify.rs                    # 新：建 sys_user_email_verify＋sys_user 唯一索引＋up 前置重複掃描（照 m011 raw 形）
├── migration/src/lib.rs                                  # 動：註冊 m014
├── entity/src/sys_user_email_verify.rs＋lib             # 新：entity（單一 PK、零 relation）
├── server/src/config.rs                                  # 動：10 新欄（SMTP 連線 5〔host/port/starttls/username/password〕＋寄件身分 4＋email_verify_secret；username 與 subject_suffix＝不設鍵即空語意、password 恆讀）
├── server/src/state.rs                                   # 動：AppState 掛 mailer 句柄＋寄件身分組＋email_verify_secret
├── server/src/mailer/mod.rs                              # 新：transport 兩態建構（STARTTLS Required／dev 明文）＋send timeout＋驗證信組裝
├── server/src/email_verify/mod.rs                        # 新：憑據簽發/驗證純函式（claims＋code_mac）＋六位碼生成＋redis key helpers
├── server/src/validation.rs                              # 動：validate_email_format 單一守門（trim／形／長度）
├── server/src/handler/user_center.rs                     # 動：email_captcha／send_email_code／verify_email_code／unbind_email 四 handler＋UpdateProfileReq 移 userEmail＋getProfile 投影加欄
├── server/src/model/facade/sys_user.rs                   # 動：commit_verified_email／unbind_email（島 I1 鎖序＋op-log）＋is_email_verified 純函式 seam＋唯一性查詢；admin 寫入路徑掛格式守門＋唯一預檢/映射
├── server/src/router.rs                                  # 動：ROUTES +4（/userCenter/* Authed）
├── server/tests/contract.rs＋wire_schema                 # 動：+4 coverage case＋UpdateProfileReq 無 userEmail 斷言＋emailVerifiedAt 投影斷言
└── server/tests/*（新測）                                 # token 產驗/MAC/TTL/3 次/消耗；提交狀態機；唯一衝突；節流原子先佔（含並發穿透負向）與 fail-closed；日上限；admin 守門（含 Some("") 清空）；mailer 兩態建構（Tls::Required／明文）；洩漏斷言（碼與憑據不落 log/op-log/回應）；captcha ctx 語境隔離；mailpit 整合

deploy/
├── secrets.dev.enc.yaml                                  # 動：+smtp_password＋email_verify_secret（皆亂數 leaf）
├── generate-secrets.sh／preflight-secrets.sh             # 動：名冊＋REQUIRED 11→13
docker-compose.yml                                        # 動：rust-api env（SMTP/MAIL 鍵＋2 個 _FILE）＋頂層 secrets +2＋service secrets 列
docker-compose.dev.yml                                    # 動：+mailpit 服務（v1.30.6、1025 內網、127.0.0.1:8025）＋dev env 覆寫（host=mailpit、starttls=false、username 空）

base-web/（worktree；fork-delta 紀律、預期全我方檔）
├── src/views/user-center/modules/email-card.vue          # 動（我方新檔）：三件式接真＋captcha 圖＋冷卻倒數＋解綁鈕＋已驗證徽章
├── src/service/api/rev4-user-center.ts                   # 動（WRAPPER）：4 新 fetch＋updateProfile 型別收斂
├── src/typings/api/rev4-user-center.d.ts                 # 動（ADAPT）：Req/Res 型別＋emailVerifiedAt
├── src/locales/langs/{zh-tw,zh-cn,en-us}.ts＋app.d.ts    # 動：page.userCenter.* 新鍵＋backend.* 拒因鍵（圈界、(ii)/(iii) 既授權）

tools/schema-gate.py                                      # 動：STRUCT allowlist＋audit_table 變體 C 分支＋TestAuditTable＋self-test dict
docs/ops/reference-src/archetype-map.json                 # 動：sys_user_email_verify 登記（variant C）
specs/002-schema-baseline/data-model.md                   # 動：§1 表歸屬補列
docs/ops/RUNBOOK.md                                       # 動：Gmail 運維節（2SV/app password/From 硬約束/配額/改密撤銷/smtp-relay 備選）
.specify/memory/constitution.md                           # 動（親決後）：(g) 擴字串＋v1.15.0
docs/arc42/decisions/0085/0086                            # 動（親決後）：draft→accepted
```

**Structure Decision**: 後端＝簽題純函式（email_verify 模組、鏡照 captcha 模組形）＋mailer 獨立模組掛 AppState＋facade 寫端兩支（島 I1 鎖序內原子提交）＋判定單一純函式 seam（getProfile 投影與未來 SSO 共用）；handler 全落 user_center 家族。前端＝email-card 單檔改造（我方新檔、零上游 inline）。dev 拓樸＝mailpit 只進 dev override。治理重心＝(g) 擴字串 Amendment＋ADR 0085/0086＋Q8 工具聯動。

## Complexity Tracking

> 無 Constitution Check 違規——(g) 擴字串 Amendment 與 ADR 0085/0086 轉 accepted 均為治理正名路徑（親決 GATE）、非違規繞道；新表走變體 C 既有軌道；lettre 新依賴經 D7 親決釘版；本表空置。
