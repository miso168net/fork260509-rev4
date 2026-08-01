# Tasks: 020-email-verify-smtp 帳號 email 驗證＋SMTP 寄信基建（B-028 信箱半邊兌現）

**Input**: [plan.md](./plan.md)／[spec.md](./spec.md)／[research.md](./research.md)／[data-model.md](./data-model.md)／[contracts/](./contracts/email-verify-contracts.md)／[quickstart.md](./quickstart.md)
**Branch**: `020-email-verify-smtp`

## Format: `[ID] [P?] [Story?] Description`

- **[P]**＝可並行（不同檔、無未完相依）；**[USn]**＝所屬 user story（Setup／Foundational／Polish 無 story 標）。
- 每任務含明確檔案路徑。TDD：各 US 測試先行（紅）→實作（綠）。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- ★rust build/test **一律容器內**（host 無 toolchain）、**單一 cargo 進程**（絕不平行多 cargo）。
  ｜`docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server -- --test-threads=1'`
- ★review agent **只讀不寫** repo 檔；findings 只放回傳訊息。
- ★**絕不 push／merge**（finishing 階段才議、需 user 明確同意）；tasks 不得排入 push/merge。
- ★base-web worktree commit **不加 `--no-verify`**（019 已廢止舊慣例——hooksPath 指外層即結構性
  旁路 husky、`--no-verify` 會同時繞過機密掃描＝ADR 0082 決策 5）；`.vue` template 標記用
  `<!-- -->`（L-119）。
- ★fork-delta：本刀**預期全我方檔**（email-card.vue＝rev4 新檔、rev4-user-center.{ts,d.ts}、locale
  純插入新鍵圈界）；若施工遇上游既有行必要 inline→**status 回 blocked 升級主線**（plan Q2 授權
  邊界）、絕不擅改；每次 base-web 改動跑 `python3 tools/fork-delta-lint.py`（★python3 直跑、bash
  假紅 L-143）。
- ★三重不洩（FR-015）：驗證碼明文與 verifyToken **絕不落**伺服器日誌／op-log payload／API 回應
  （發碼回應僅 verifyToken）；smtp_password 絕不落日誌／回應。
- ★單一 seam 零分叉：已驗證判定＝`is_email_verified` 純函式（getProfile 投影／未來 SSO 共用）；
  信箱格式＝`validate_email_format`（sendEmailCode／addUser／updateUser 三處共用）。
- ★updateUser 信箱欄契約（011 FR-007、絕不 blank_to_none）：`None`＝不動；`Some("")`＝清空、
  跳過守門；`Some(非空)`＝過守門。
- ★發碼固定序不得重排（data-model §3）：captcha gate（ctx=="email" 斷言）→格式→**節流原子先佔**
  （SET NX cd→INCR day）→唯一預檢（命中**不回補**）→寄信（失敗盡力回補）→簽發憑據；節流常數
  寫死程式碼、不入 system_settings。
- ★captcha claims `ctx` 欄兩端斷言（login 端 issue/gate 同步帶 "login"）；**login 行為與判定序
  零改動**（島 E 零觸及、既有 login captcha 測試零紅為機器證）。
- ★**零新錯誤碼**（2222 reuse＋msg=i18n key、逐鍵名冊＝contracts C8）；拒因復用不自然→回報
  主線、絕不自行造碼。
- 每執行單元收尾：worktree 內 commit →**立即**回外層 bump submodule pin（兩段式 commit）。
  ★外層順序：**先 `git add rust-api`／`git add base-web` 再 `python3 tools/docs-sync.py generate`**
  （反序被 L1 擋）。
- ★新 i18n key 後、CDP 前必 **restart base-web**（vite 未必熱載、L-015）；m014 落庫後 restart
  rust-api；整合測試前確認 mailpit healthy（`curl -s http://127.0.0.1:8025/readyz`）。
- 活書（ARCHITECTURE.md）as-built 更新與 B-028 條目改寫**不排入任何 Phase**——落收刀簿記 commit。

---

## ★★ 治理前置 GATE（起 Phase 2 起全部任務前 MUST 完成）

**(g) 擴字串＋§I.6 變體 C 釋義＋ADR 0085/0086——治理級決定不得以主線裁決名義烤進 agent prompt
（L-146）；GATE 由主線 AskUserQuestion 親決、非 workflow agent。**
→ 親決 gate 照 013/014/015 判例提前（Phase 1 純函式 seam 與寄信基建外圍不依賴、可先行）。

MUST 完成（§V.2 程序、user 親決）：
1. **ADR 0085/0086 → accepted**（draft 已收斂 clarify 四拍板＋plan 對抗式驗證校正）。
2. `.specify/memory/constitution.md` §III.2 **(g) 擴字串**（「＋驗證 UI 佔位」→「＋信箱驗證流
   〔發碼／回填驗證／解除綁定／其 captcha 取題〕＋對應 i18n key」、page.userCenter 鍵集敘明擴至
   本刀新集合——research R11 字面）＋**§I.6 變體 C upsert 釋義句**（1:1 已驗證值衛星表之 upsert
   刷新＝重驗事件覆寫、verified_at 即其時戳、不設 updated_{at,by}——比照 J3 釋義形）＋
   **bump v1.14.0→v1.15.0**。
3. **獨立 commit** `docs(constitution): amend (g) 擴字串信箱驗證流＋§I.6 變體 C upsert 釋義`
   （憲法＋ADR 同 commit）＋`python3 tools/docs-sync.py generate`。

起 Phase 2 前確認：`grep -n '^- 1\.15\.0' .specify/memory/constitution.md` 有值即可。

---

## Phase 1: Setup（純函式 seam＋寄信基建外圍先立；治理 GATE 前可先行）

**Purpose**: 不依賴新表與親決的地基全就位。

- [ ] T001 判定純函式 `is_email_verified`（★純量簽名〔analyze I2 定案〕：吃 `user_email` 與
  `verified_email`／`verified_at` 純量參數、回 Option 時刻；衛星 entity 解構歸呼叫端——Phase 1
  零表依賴可全綠、data-model §2 已同步勘正）＋`validate_email_format` 單一守門（trim／基本形／
  長度 ≤254）＋單元測試（判定三態＋大小寫變體＋格式正負向＋空值語意）in
  `rust-api/server/src/model/facade/sys_user.rs`＋`rust-api/server/src/validation.rs`
- [ ] T004 [P] lettre 0.11.22 釘版（`default-features=false`＋features 見 research R1）in
  `rust-api/server/Cargo.toml`（workspace 依現慣例）＋容器內 `cargo build` 綠（依賴解析證）
- [ ] T005 [P] SOPS +2 key 全鏈：`smtp_password`＋`email_verify_secret` 皆亂數 leaf（★不用
  CHANGE-ME——config 對其 panic）in `deploy/secrets.dev.enc.yaml`＋`deploy/generate-secrets.sh`
  名冊＋`deploy/preflight-secrets.sh` REQUIRED 11→13；本機重生→依 RUNBOOK §15 回寫→解密落
  `$SECRETS_DIR`→preflight 13 檔綠
- [ ] T006 [P] compose 面：base 六常設 plain env（Gmail 形）＋2 `_FILE`＋頂層/service secrets +2
  （★username 與 subject_suffix **base 不設鍵**）in `docker-compose.yml`；mailpit 服務
  （`axllent/mailpit:v1.30.6`、1025 內網、`127.0.0.1:8025`）＋rust-api dev 七鍵覆寫 in
  `docker-compose.dev.yml`；up 後 `curl -s http://127.0.0.1:8025/readyz` 200

**Checkpoint**: preflight 13 檔綠；mailpit readyz 200；容器內 cargo build 綠；T001 單元測試綠。

## Phase 2: Foundational（表＋config＋mailer＋憑據底座就位）— BLOCKING ★治理 GATE 後

**Purpose**: 所有端點與寫入的前置底座。★T002/T003 自 Phase 1 移入（analyze I1、三鏡頭同抓）：
與 m014 同單元、**收尾同 commit**——兌現 data-model §1「工具聯動 m014 同 commit、缺一即紅」
字面、杜絕「已登記表未建」中間態 audit 紅、且 audit 分支語意於治理 GATE 親決後才施工（L-146）。

- [ ] T002 [P] `tools/schema-gate.py` 工具聯動：STRUCT_ADDITIVE_ALLOWLIST 加表級
  `sys_user_email_verify`＋**index 級 `(index, sys_user, sys_user_user_email_active_uniq)`**＋
  audit_table 加 `elif variant=="C" and table=="sys_user_email_verify":` 分支（檢 created_at NN
  ＋禁 updated_*/deleted_*；★分支語意以 GATE 親決之 §I.6 釋義句定稿為準、翻案同單元回改）＋
  TestAuditTable 案例＋self-test 精確集合 dict 同步 in `tools/schema-gate.py`
- [ ] T003 [P] archetype-map 登記＋baseline data-model 歸屬補列（variant C、note 記 verified_at
  upsert 刷新／created_{at,by} 首建不動／零 FK／不存驗證碼）in
  `docs/ops/reference-src/archetype-map.json`＋`specs/002-schema-baseline/data-model.md`
- [ ] T007 migration `m014_email_verify`：up＝**前置重複掃描**（active 列 lower(user_email)
  HAVING count>1→Err 印清單）→建 `sys_user_email_verify`（DDL 逐字＝data-model §1）→
  `sys_user_user_email_active_uniq` 唯一索引；down 對稱 DROP in
  `rust-api/migration/src/m014_email_verify.rs`＋Migrator 註冊 in `rust-api/migration/src/lib.rs`
- [ ] T008 entity `sys_user_email_verify`（單一 PK Model、零 relation）in
  `rust-api/entity/src/sys_user_email_verify.rs`＋`mod` 註冊
- [ ] T009 config 10 新欄（兩特例＝不設鍵即空語意；port/starttls parse fail-loud）＋AppState 3
  新件（mailer 句柄＋mail_identity＋email_verify_secret）＋config 缺值 panic 測試沿既有範式 in
  `rust-api/server/src/config.rs`＋`rust-api/server/src/state.rs`
- [ ] T010 mailer 模組：兩態建構（starttls=true→`starttls_relay` `Tls::Required`／false→明文
  builder）＋timeout 15s＋username 非空才掛 credentials＋驗證信組裝（純文字、六位碼＋有效期、
  主旨帶 suffix、zh-TW 文案）＋**兩態建構單元測試**（SC-008 載體、拆分支即紅）＋非 ASCII
  顯示名標頭編碼斷言＋suffix 空值主旨組裝斷言（spec edge case 載體、analyze C2）in
  `rust-api/server/src/mailer/mod.rs`
- [ ] T011 captcha `ctx` 欄（additive：issue/verify 帶 ctx、login 端 issue 與 captcha_gate 同步
  帶 "login"、★既有 login captcha 測試零紅＝行為零改動機器證）in
  `rust-api/server/src/captcha/mod.rs`＋`rust-api/server/src/throttle/mod.rs`＋
  `rust-api/server/src/handler/throttle.rs`；email_verify 模組（憑據簽發/驗證純函式＋
  `code_mac=SHA256(secret‖nonce‖code)`＋OsRng 六位碼＋redis key helpers 含 **TTL 讀取新原語**）
  ＋單元測試（token 產驗/MAC secret 參與/TTL leeway=0/uid 綁定/ctx 語境隔離）in
  `rust-api/server/src/email_verify/mod.rs`＋`rust-api/server/src/redis/mod.rs`
- [ ] T012 m014 落庫＋restart rust-api＋`schema-gate.py gate1/gate2/audit` 三綠（新表＋新索引
  零漂移、變體 C 分支過）＋docs-sync refresh 快照（015 U2 先例：落庫收單時 refresh 收錄新表）

**Checkpoint**: 容器內 cargo lib 全綠（seam／格式／token／mailer 兩態／ctx 隔離）；schema-gate
三子命令＋`--self-test` 綠（T002 新分支與 index 項案例過）。

## Phase 3: User Story 1 - 本人綁定／變更信箱並完成驗證 (P1) 🎯 MVP

**Goal**: 四新端點＋facade 寫端＋updateProfile 收斂＋email-card 接真——驗證即提交全鏈。

**Independent Test**: dev 棧發碼→mailpit 收件人條件撈信抽碼→回填→DB 斷言 email＋衛星列＋
op-log；錯 3 次廢；解綁；重放/跨帳號拒；洩漏零命中。

### 後端（rust-api）

- [ ] T013 [US1] 測試先行（紅）：契約面——4 新 route coverage case＋`UpdateProfileReq` **無
  userEmail 欄斷言**（SC-004 契約級）＋`emailVerifiedAt` 投影正負向＋wire_schema 重擷取 in
  `rust-api/server/tests/contract.rs`＋`rust-api/server/tests/wire_schema.rs`
- [ ] T014 [US1] 測試先行（紅）：整合全鏈——發碼（mailpit API `search?query=to:` 撈信抽碼）→
  verify→DB 斷言（user_email＋衛星列 upsert 語意含 created_{at,by} 首建不動）＋op-log 白名單；
  錯 3 次即廢（含其後正確碼）；過期；成功憑據重放；跨帳號；鎖內唯一終判；解綁（衛星留存＋
  emailNotBound）；**洩漏斷言**（log 與 op-log payload 零六位碼零憑據、SC-007）in
  `rust-api/server/tests/email_verify.rs`（新測檔）
- [ ] T015 [US1] handler：`email_captcha`（ctx="email"、subject=uid、回 captchaId/captchaImg）＋
  `send_email_code`（固定序：captcha gate→格式→原子先佔→唯一預檢不回補→寄信→失敗回補→簽發）
  in `rust-api/server/src/handler/user_center.rs`＋ROUTES +2 in `rust-api/server/src/router.rs`
- [ ] T016 [US1] handler：`verify_email_code`＋`unbind_email`＋facade 寫端兩支
  `commit_verified_email`／`unbind_email`（`advisory_lock_user_db`＋
  `find_active_by_id_for_update` 鎖內重驗＋唯一終判＋used SET NX 消耗先於效果＋upsert 衛星＋
  op-log 同 txn）in `rust-api/server/src/model/facade/sys_user.rs`＋handler＋ROUTES +2（T014 轉綠）
- [ ] T017 [US1] `UpdateProfileReq` 移 userEmail（四→三欄）＋getProfile 投影 `emailVerifiedAt`
  （衛星主鍵查＋is_email_verified seam）in `rust-api/server/src/handler/user_center.rs`（T013 轉綠）

### 前端（base-web）

- [ ] T018 [P] [US1] typings＋service：4 新 DTO（captchaId/captchaImg 欄名）＋`emailVerifiedAt`
  ＋UpdateProfileReq 同步刪欄 in `base-web/src/typings/api/rev4-user-center.d.ts`；4 新 fetch＋
  updateProfile 型別收斂 in `base-web/src/service/api/rev4-user-center.ts`
- [ ] T019 [US1] email-card.vue 改造（contracts C10 動線：徽章含時刻＋captcha 圖點擊換題與答錯
  自動重取＋發送→冷卻倒數（純前端 60s、拒因 remainingSeconds 重建）＋回填→驗證→emit saved
  重拉＋解綁鈕確認（未綁定不顯示）＋獨立儲存鈕退場）in
  `base-web/src/views/user-center/modules/email-card.vue`

**Checkpoint**: 容器內 cargo 全綠＋typecheck＋fork-delta-lint 綠；CDP S1（快樂路徑＋洩漏子步）
＋S2（錯碼三次）＋S6（解綁＋回填恢復前半）＋S7（captcha 閘）PASS（★CDP 以行為判準、容忍
raw key——三語於 S9 統一驗、analyze C1）。

## Phase 4: User Story 2 - admin 端語意與驗證態呈現 (P2)

**Goal**: admin 格式守門（無值未變豁免）＋唯一衝突明確拒因；導出語意實彈。

**Independent Test**: admin 改已驗證會員信箱→未驗證；改回→恢復；填重複/怪值→明確拒因；
存量怪值觸及被擋、同表單修正自癒。

- [ ] T020 [US2] 測試先行（紅）：addUser（blank_to_none 後 Some 才驗＋唯一預檢＋索引兜底映射
  emailTaken）；updateUser 三態（None 不動／Some("") 清空跳守門／Some 非空驗）＋無豁免（psql
  植入怪值→重送原值被擋）＋鎖內唯一預檢；admin 改值後導出翻假／改回恢復 in
  `rust-api/server/tests/admin_email_guard.rs`（新測檔、analyze U2 定錨）
- [ ] T021 [US2] admin 寫入路徑掛守門＋DbErr unique violation 映射 2222 `biz.user.emailTaken`
  in `rust-api/server/src/handler/user.rs`＋`rust-api/server/src/model/facade/sys_user.rs`
  （T020 轉綠；唯一查詢 helper 沿 T016 共用）

**Checkpoint**: cargo 全綠；CDP S5（admin 語意全子步含怪值自癒）＋S6 後半（admin 回填→徽章
自動恢復）PASS（行為判準、容忍 raw key 同上）。

## Phase 5: User Story 3 - 節流與濫用防護 (P3)

**Goal**: 節流深度驗證（原子先佔語意的機器背書）；不足處修 send 實作。

**Independent Test**: 冷卻攜秒數；日上限第 11 次拒；並發 k 筆恰 1 封；寄信失敗回補；redis 停機
fail-closed＋告警。

- [ ] T022 [US3] 測試先行（紅→綠）：冷卻先佔正負向（搶佔失敗攜 remainingSeconds）；日上限
  （redis 預置計數→第 11 次拒＋超限 DECR 回補證）；**並發穿透負向**（k 筆預解題突發→恰 1 封、
  SC-003 載體）；寄信失敗回補（mailpit 停→emailSendFailed→cd/day 已回補→立即可重試）；redis
  停機→發碼與 verify 皆 fail-closed＋`warn_degraded`；唯一預檢命中不回補 in
  `rust-api/server/tests/email_verify.rs`（擴充；紅則修 `send_email_code` 實作）

**Checkpoint**: cargo 全綠；CDP S3（冷卻＋重整重建＋日上限）＋S8（fail-closed 自癒）PASS
（行為判準、容忍 raw key 同上）。

## Phase 6: User Story 4 - 介面三語化 (P4)

**Goal**: 本刀全部新鍵三語＋Schema 鏡像機器一致。

**Independent Test**: 三語各切一次走 US1 全流程＋admin 拒因＋解綁→零 raw key。

- [ ] T023 [US4] 三語 locale 全量新鍵（`backend.*` 12＋2 逐鍵名冊＝contracts C8、emailCooldown
  攜 `{remainingSeconds}` 佔位；`page.userCenter.*` 徽章/解綁/captcha/倒數/成功提示；
  `comingSoon` 佔位鍵**保留不刪**〔U7 實測推翻 analyze U1「接真後零消費」前提：password-card 之
  非舊密碼驗證方式路徑的 comingSoon toast 與 phone-card 驗證碼佔位組的 comingSoon toast（皆 B-028
  另半佔位）仍為活消費者、強刪即壞卡＋typecheck 紅；刪除延後至 B-028 另半接真自然退場——主線拍板修正〕）in
  `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts`＋`App.I18n.Schema` 鏡像 in
  `base-web/src/typings/app.d.ts`（圈界）——typecheck 綠＝鏡像機器證
- [ ] T024 [US4] restart base-web＋CDP S9（三語零 raw key）PASS

**Checkpoint**: typecheck＋fork-delta-lint 綠；CDP S9 PASS。

## Phase 7: Polish & 全量驗收

**Purpose**: 運維文件＋全場景實彈＋全量閘＋final review（收刀簿記另計、不排此）。

- [ ] T025 RUNBOOK Gmail 運維節（research R3 五約束：2SV＋app password 建立、From 硬約束、
  2000 封/日、改密撤銷 app password＋重生 SOP、smtp-relay 備選；真值填法連動 §15.4）in
  `docs/ops/RUNBOOK.md`
- [ ] T026 CDP 九場景全量複跑（quickstart §CDP、含場景 4 唯一衝突與場景 5 怪值子步）＋負向自證
  ——★以 **quickstart §負向自證全條**為唯一名冊（單源、analyze C3；含 m014 前置掃描紅與唯一
  索引直插紅兩條）各即紅＋資料清理（quickstart §資料清理）
- [ ] T027 全量閘：容器內 `cargo test -p server -- --test-threads=1`＋
  `cargo test --test contract --test wire_schema --test email_verify -- --test-threads=1`＋
  `schema-gate.py gate1/gate2/audit`＋`--self-test`＋typecheck＋
  `python3 tools/fork-delta-lint.py`＋`bash deploy/preflight-secrets.sh`＋
  `python3 tools/docs-sync.py check` 全綠
- [ ] T028 final holistic review（異質雙審：安全狀態機鏡頭＋治理合規鏡頭；只讀不寫、findings
  回主線）→ 三分流（修／轉 B-NNN／won't-fix ADR）

**Checkpoint**: 全量閘綠＋final review 零 merge-blocker → finishing（push/merge 需 user 同意）。

---

## 相依圖與並行機會

- **Phase 1**（T001、T004~T006）：不依賴治理 GATE、可先行；T004/T005/T006 [P] 並行
  （不同檔、無 cargo 互撞——T004 的 build 驗證單獨收尾跑）。
- **治理 GATE**（(g) 擴字串＋§I.6 釋義＋ADR 0085/0086、主線 AskUserQuestion 親決）→ 起 Phase 2。
- **Phase 2**（T002/T003＋T007~T012）BLOCKING：T002/T003 [P]（工具與登記、★與 m014 同單元
  收尾同 commit——analyze I1）；T007→T008 序列（表→entity）；T009→T010 序列（config→
  mailer）；T011 與 T009/T010 不同檔可交錯但 cargo serial、單元內順跑；T012 收尾。
- **Phase 3 US1**（MVP）：後端 T013/T014 紅先行→T015→T016→T017 轉綠；前端 T018 [P]（與後端
  不同 worktree 可並行）→T019（消費 T015/T016 端點、聯調需後端就位）。
- **Phase 4 US2**：依賴 Phase 2（表＋seam）＋T016（唯一查詢 helper 共用）；與 US3/US4 互獨立。
- **Phase 5 US3**：依賴 T015（send 實作在位、深度測試打其固定序）。
- **Phase 6 US4**：依賴 US1/US2 拒因鍵集定形；T023 統一收口。
- **Phase 7**：全量、序列收尾。

## 執行單元建議切分（Workflow 編排、每單元一支）

1. **U1 地基**（T001、T004~T006）：seam＋lettre 釘版＋secrets 鏈＋compose/mailpit
   〔治理 GATE 前可跑〕。
2. **[治理 GATE]** 主線 AskUserQuestion 親決 (g) 擴字串＋§I.6 釋義＋ADR 0085/0086→accepted＋
   bump v1.15.0→獨立 commit（非 workflow）。
3. **U2 底座**（T002/T003＋T007~T012）：工具聯動與登記（GATE 後施工、與 m014 同單元收尾同
   commit）＋m014＋entity＋config/state＋mailer＋captcha ctx＋email_verify 模組＋落庫三綠。
4. **U3 後端驗證鏈**（T013~T017）：契約與整合紅先行→四端點＋facade 寫端＋updateProfile 收斂。
5. **U4 前端驗證鏈**（T018~T019）：typings/service→email-card 改造（與 U3 可並行起、聯調在後）。
6. **U5 admin 守門**（T020~T021）。
7. **U6 節流深度**（T022）。
8. **U7 三語**（T023~T024）。
9. **U8 全量驗收**（T025~T028）：RUNBOOK＋CDP 九場景＋全量閘＋final review。

## MVP 範圍

**US1（Phase 3）＝MVP**：驗證即提交全鏈（captcha→發碼→mailpit 收信→回填→原子提交＋衛星表＋
解綁）落地即兌現 B-028 信箱半邊核心語意與 SMTP 寄信能力；US2 admin 守門、US3 節流深度、US4
三語為增量（節流實作本體已隨 US1 固定序落地、US3 為其機器背書深度）。
