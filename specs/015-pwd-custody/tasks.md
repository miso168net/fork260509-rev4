# Tasks: 015-pwd-custody 隨機產密＋密碼經手表＋首登強制換密（B-030 兌現）

**Input**: [plan.md](./plan.md)／[spec.md](./spec.md)／[research.md](./research.md)／[data-model.md](./data-model.md)／[contracts/](./contracts/pwd-custody-contracts.md)／[quickstart.md](./quickstart.md)
**Branch**: `015-pwd-custody`

## Format: `[ID] [P?] [Story?] Description`

- **[P]**＝可並行（不同檔、無未完相依）；**[USn]**＝所屬 user story（Setup／Foundational／Polish 無 story 標）。
- 每任務含明確檔案路徑。TDD：各 US 測試先行（紅）→實作（綠）。

## ★不可違反（烤進每個執行單元的 agent prompt）

- ★書面產物（report／blocker／程式碼註解／文件）一律 **zh-TW**（L-113）。
- ★rust build/test **一律容器內**（host 無 toolchain）、**單一 cargo 進程**（絕不平行跑多個 cargo）。
  ｜`docker exec rev4-admin-rust-api-1 sh -c 'cd /app && cargo test -p server -- --test-threads=1'`
- ★review agent **只讀不寫** repo 檔；findings 只放回傳訊息。
- ★**絕不 push／merge**（收尾 finishing 階段才議、且需 user 明確同意）；tasks 不得排入 push/merge。
- ★base-web worktree commit 一律 `--no-verify`；`.vue` template 標記用 `<!-- -->`（L-119）。
- ★fork-delta：**修改型 inline**（guard/route.ts、auth store、manage/user index.vue、user-operate-drawer.vue、password-card.vue、build/plugins/router.ts——動到基線既有行）每處被動行標 `原行:` 逐字基線原文；**新增型圈界**（產密浮層元件、force-change-pwd 頁、rev4-pwd-custody.d.ts、locale 三檔與 app.d.ts 之純插入新鍵——I18N-WIRING 歷刀同形）零原行；判準＝**基線檔實況為準：純插入行＝圈界、動到既有行＝原行**（analyze I3 裁定）；每次改動跑 `python3 tools/fork-delta-lint`（★python3 直跑、bash 假紅 L-143）。
- ★島 I5 密碼三重不洩：經手表結構性零密碼欄；op-log payload 零密碼；隨機密碼**本地 CSPRNG**（`crypto.getRandomValues`、絕不 Math.random）＋伺服器回應零密碼。
- ★密碼驗證複用單一驗證點零分叉；**冷卻＝端點固有規則、排各端點既有拒因全過之後、UPDATE 前、鎖內**，MUST NOT 入 `validate_against_policy`。
- ★判定規則收斂為**單一純函式** `need_change_pwd`（三處共用：getUserInfo／pwd_gate_mw／測試）——絕不各處內聯 SQL（分叉＝014 U9 同類坑）。
- ★**「全刪」範圍恆＝`WHERE user_id=標的`**（絕非 created_by）。
- 每執行單元收尾：worktree 內 commit →**立即**回外層 bump submodule pin（兩段式 commit）。
  ★外層順序：**先 `git add rust-api`／`git add base-web` 再 `python3 tools/docs-sync generate`**（反序被 L1 擋）。
- ★新 i18n key 後、CDP 前必 **restart base-web**（vite 未必熱載、L-015）；migration 落庫後 restart rust-api。
- 活書（ARCHITECTURE.md）as-built 更新**不排入任何 Phase**——落收刀簿記 commit。
- ★**零新錯誤碼**（2222 reuse）／零新 casbin seed（「密碼」動作沿重設密碼按鈕碼）；若某拒因復用不自然→**回報主線、絕不自行造碼**。

---

## ★★ 治理前置 GATE（起 Phase 2 起全部任務前 MUST 完成）

**新用途 (k)＋Q9 島 I 細項＋ADR 0067——治理級決定不得以主線裁決名義烤進 agent prompt（L-146）；GATE 由主線 AskUserQuestion 親決、非 workflow agent。**
→ 親決 gate 照 013/014 判例提前（Phase 1 純測試骨架與工具聯動不依賴、可先行）。

MUST 完成（§V.2 程序、user 親決）：
1. **ADR 0067 → accepted**（經手表模型＋鎖態 token 硬閘選型；★轉 accepted 前 draft 已收斂 specify 期親決——冷卻一體適用零例外＋攜剩餘秒數、豁免殘句已刪〔analyze I5〕）
2. `.specify/memory/constitution.md` §III.2 **新用途 (k)**（枚舉見 research R5：強制改密頁＋route guard 攔截控制流＋auth store inline＋manage「密碼」動作與浮層＋add 抽屜與 user-center 改密卡隨機鈕＋「＋對應 i18n key」字樣＋**兩檔位錨**——產密浮層共用元件（src/components/ 新檔、新增型圈界）與 constantRoutes 名單觸點（build/plugins/router.ts、修改型）〔analyze U1〕；(a)/(g)/(h) 擴字面併敘＋**§I.2 constantRoutes 射程釋義一句**（constant route 集合可經 §III.2 授權新增、builtin 三頁與 Casbin 豁免語意不變〔analyze C1〕））＋**Q9 島 I 細項擴充字面**（經手判定／寫入規則／冷卻／硬閘白名單語意＋硬閘每請求 EXISTS 與島 I2「MUST NOT 每請求活性判定」射程區隔論證）＋**九/十用途失步勘誤**＋**bump v1.13.0→v1.14.0**
3. **獨立 commit** `docs(constitution): amend 新用途 (k) 首登強制換密頁＋guard 攔截控制流`（憲法＋ADR 同 commit）＋`python3 tools/docs-sync generate`

起 Phase 2 前確認：`grep -n '^- 1\.14\.0' .specify/memory/constitution.md` 有值即可。

---

## Phase 1: Setup（後端測試骨架＋工具聯動先立）

**Purpose**: 判定純函式 seam 與工具閘先立（不依賴治理 GATE、可先行）。

- [ ] T001 判定純函式 `need_change_pwd(conn, user_id) -> Result<bool>` seam（`EXISTS(... WHERE user_id=$1 AND created_by<>$1)`）＋單元測三態（零列/純自改列/含他人經手列）in `rust-api/server/src/model/facade/sys_user.rs`——完成判準＝簽章＋三態測試骨架（`#[ignore]` 標記註明待表）編譯綠；**Phase 2 T005 接線真表後取消 ignore 轉綠**（實庫測試無自然 stub 縫、analyze A2 裁定）
- [ ] T002 [P] `tools/schema-gate` 工具聯動：`audit_table` 加 `elif variant=="C" and table=="sys_pwd_custody":` 分支（檢 created_at NOT NULL＋禁 updated_*/deleted_* 出現）＋STRUCT_ADDITIVE_ALLOWLIST 加 sys_pwd_custody＋SEED_ADDITIVE_ALLOWLIST 加 `password_change_min_interval`＋TestAuditTable 案例＋self-test dict 同步 in `tools/schema-gate`
- [ ] T003 [P] archetype-map 登記＋baseline data-model 歸屬補列（variant C、note 記 created_at 語意/零 FK/不存密碼）in `docs/ops/reference-src/archetype-map.json`＋`specs/002-schema-baseline/data-model.md`

**Checkpoint**: `python3 tools/schema-gate --self-test` 綠（新分支案例過）。

## Phase 2: Foundational（migration＋entity＋表就位）— BLOCKING

**Purpose**: 經手表落庫、entity 可用（所有寫入/判定/硬閘的前置）。★治理 GATE 後。

- [ ] T004 migration `m011_pwd_custody`：up＝建 sys_pwd_custody（複合 PK、零 FK、created_at NN default now()、無 updated_*/deleted_*）＋seed system_settings `password_change_min_interval`='60'（WHERE NOT EXISTS 防重）；down 對稱 DROP＋seed DELETE in `rust-api/migration/src/m011_pwd_custody.rs`＋Migrator 註冊 in `rust-api/migration/src/lib.rs`
- [ ] T005 entity `sys_pwd_custody`（複合 PK Model、零 FK relation）in `rust-api/entity/src/sys_pwd_custody.rs`＋`mod` 註冊；T001 判定函式接線至真表
- [ ] T006 migration 落庫＋restart rust-api＋`schema-gate gate1/gate2/audit` 三綠（新表結構零漂移＋settings seed 定稿＋變體 C 分支過）

**Checkpoint**: 容器內 `cargo test -p server --lib need_change_pwd` 判定三態綠；schema-gate 三子命令綠。

## Phase 3: User Story 1 - 管理員經手設密→會員首登強制換密 (P1) 🎯 MVP

**Goal**: 經手寫入三入口＋getUserInfo 投影＋API 硬閘＋前端 guard/強制頁/登出——首登強制換密全鏈。

**Independent Test**: admin 重設會員密碼→會員登入落強制改密頁＋token 直打列表 API 被 2222→改密成功→自動登出→新密重登暢行；seed 三帳號零影響。

### 後端（rust-api）

- [ ] T007 [US1] 測試先行（紅）：三寫入路徑經手列斷言（insert→(new,admin)／reset_password operator≠target→upsert(target,admin)／reset_password operator==target→全刪+寫(self,self)／change_own_password→全刪+寫(self,self)）＋seed 帳號零列＋**FR-016 pin**（軟刪標的後 custody 列仍在、復原後 need_change_pwd 判定不變——一斷言、防後續刀無聲加清理〔analyze G1〕）in `rust-api/server/tests/`（新測檔）
- [ ] T008 [US1] facade 三入口經手寫入（`insert` append／`reset_password` operator 分支 upsert-or-本人改路徑〔沿既有 keep-sid 自我分支點〕／`change_own_password` 全刪+寫自列）——同交易＋鎖內原子；「全刪」恆 `WHERE user_id=標的` in `rust-api/server/src/model/facade/sys_user.rs`（T007 轉綠）
- [ ] T009 [US1] getUserInfo 加 `needChangePwd`（UserInfo struct 加 `need_change_pwd:bool` wire camelCase＋既有 sys_user 重讀旁 +1 need_change_pwd 呼叫）＋contract/in-crate 正負向斷言（含他人經手→true／零列→false）in `rust-api/server/src/handler/auth.rs`＋`rust-api/server/tests/contract.rs`
- [ ] T010 [US1] 測試先行（紅）：pwd_gate_mw——**六白名單路徑逐一正向放行斷言**（changePassword／getPasswordPolicy／getUserInfo／getUserRoutes／getProfile／isRouteExist；漏列任一即強制頁自身癱瘓〔analyze G2〕）＋負向封鎖斷言（getUserList→2222 mustChangePassword）＋兩子 router 皆掛（**帶權限 manage 端點亦擋＝casbin policy 子 router 亦掛閘；getPasswordPolicy 屬白名單放行**——措辭消歧）in `rust-api/server/tests/`（新測檔）
- [ ] T011 [US1] `pwd_gate_mw`（讀 Claims.uid→need_change_pwd→白名單 path const 比對→2222 `biz.auth.mustChangePassword`）in `rust-api/server/src/middleware/`（新檔或 mod.rs）＋掛 `build()` authed＋policy 兩子 router（enforce 後、access_log 內側）in `rust-api/server/src/router.rs`（T010 轉綠）

### 前端（base-web）

- [ ] T012 [P] [US1] 新增型：`rev4-pwd-custody.d.ts`（`Api.Auth.UserInfo` needChangePwd?:boolean 成員級 declaration merging；不動凍結 auth.d.ts）in `base-web/src/typings/api/rev4-pwd-custody.d.ts`
- [ ] T013 [US1] auth store 承載 `needChangePwd`（修改型 inline `原行:`、optional 免補初值、getUserInfo 回填）in `base-web/src/store/modules/auth/*`
- [ ] T014 [US1] 強制改密 constant route 頁（新增型：舊密+新密+確認+隨機鈕+登出鈕；成功→清 store needChangePwd+呼 logout→登入頁；政策 rules 用共用 hook；userName 走 getProfile 真帳號；**說明區強調「複製後送出」提醒**〔隨機值未抄存即送出→鎖出、analyze G6〕）in `base-web/src/views/_builtin/force-change-pwd/index.vue`＋constantRoutes 名單一行（修改型 `原行:`）in `base-web/build/plugins/router.ts`——**顯式前置＝T016**（浮層元件＋共用 hook 先就位、analyze I1）
- [ ] T015 [US1] route guard 全域攔截（修改型 inline `原行:`：isLogin+needChangePwd+目的地≠強制頁→改寫導向；置於路由存在性解析之先）in `base-web/src/router/guard/route.ts`

**Checkpoint**: 容器內 cargo 全綠（三寫入/硬閘/getUserInfo 正負向）＋typecheck＋fork-delta-lint 綠；CDP S1（首登強制+硬閘實彈+登出重登——**以既有「重設密碼」手輸入口執行主鏈；浮層入口段於 Phase 4 checkpoint 與 T024 補驗**〔analyze I2〕）＋S4（seed 零影響）PASS。

## Phase 4: User Story 2 - 隨機密碼產生浮層（三掛載點） (P2)

**Goal**: 產密浮層元件（CSPRNG）＋三掛載點；改密卡政策 rules 抽共用 hook。

**Independent Test**: 三掛載點各「產生」→值合政策→複製同值→帶入送出成功；回應零密碼。

- [ ] T016 [US2] 產密浮層元件（新增型：產生〔CSPRNG＋構造性滿足 getPasswordPolicy 7 鍵〕/唯讀 input/顯示密碼切換/複製/帶入 emit）in `base-web/src/components/`（新檔）＋buildPolicyRules 抽共用 hook（password-card 內重排、供強制頁與浮層共用）
- [ ] T017 [US2] 掛載點①add 抽屜密碼欄旁「隨機密碼」鈕（修改型 inline `原行:`、帶入密碼欄）in `base-web/src/views/manage/user/modules/user-operate-drawer.vue`
- [ ] T018 [US2] 掛載點②operate 欄「密碼」動作（修改型 inline `原行:`：NDropdown/操作欄加項、沿用「重設密碼」按鈕權限碼、浮層唯讀不可手輸、確認送出 resetUserPassword）in `base-web/src/views/manage/user/index.vue`
- [ ] T019 [US2] 掛載點③user-center 改密卡儲存前「隨機密碼」鈕（修改型 inline `原行:`、帶入新密+確認兩欄、走自助改密不觸發強制、(g) 射程）in `base-web/src/views/user-center/modules/password-card.vue`

**Checkpoint**: typecheck＋fork-delta-lint 綠；CDP S2（手輸重設觸發）＋S3（建帳觸發）＋S6（user-center 自助不觸發、含隨機鈕）PASS；三掛載點回應零密碼。

## Phase 5: User Story 3 - 設密冷卻（頻率保護） (P3)

**Goal**: 三入口鎖內冷卻檢查（一體適用零例外、攜剩餘秒數）＋settings fail-default。

**Independent Test**: 同對連兩次設密（<N）→第二次拒+剩餘秒數；滿 N 過；N=0 不限；不同 admin 同標的不受限；失敗嘗試不計。

- [ ] T020 [US3] 測試先行（紅）：冷卻正負向（未滿拒/已滿過/N=0 停用/不同操作者不受限/失敗嘗試不計/強制頁自改亦受冷卻/**settings 缺鍵或值非法→fail-default 60 運作、設密不被阻斷**〔analyze G5〕）in `rust-api/server/tests/`（新測檔）
- [ ] T021 [US3] 冷卻檢查插入三入口（鎖內、各端點既有拒因全過之後、UPDATE 前；pair created_at 未滿 N→2222 `biz.user.pwdSetTooFrequent` 攜剩餘秒數〔BizData 帶值〕；settings 單鍵讀缺鍵 fail-default 60、0 停用）in `rust-api/server/src/model/facade/sys_user.rs`（T020 轉綠；依賴 US1 T008 三寫入路徑已就位）

**Checkpoint**: 容器內 cargo 冷卻正負向全綠；CDP S5（冷卻連按+剩餘秒數+N=0）PASS。

## Phase 6: User Story 4 - 介面三語化 (P4)

**Goal**: 本刀全部新鍵三語＋Schema 鏡像機器一致。

**Independent Test**: 三語各切一次走 US1 全流程＋三掛載點浮層＋settings 新項→零 raw key。

- [ ] T022 [US4] 三語 locale 全量新鍵（產密浮層 5 鍵/manage「密碼」動作標籤/強制頁 route+標題+說明〔含「複製後送出」提醒語意、analyze G6〕+成功+登出鈕/`backend.biz.auth.mustChangePassword`/`backend.biz.user.pwdSetTooFrequent`〔攜剩餘秒數佔位〕/settings `passwordChangeMinInterval` 標籤；zh-TW 在地化正體）in `base-web/src/locales/langs/{zh-tw,zh-cn,en-us}.ts`＋`App.I18n.Schema` 鏡像 in `base-web/src/typings/app.d.ts`（`rev4-inline` 圈界）——typecheck 綠＝鏡像機器證
- [ ] T023 [US4] restart base-web＋CDP S7（三語零 raw key）PASS

**Checkpoint**: typecheck＋fork-delta-lint 綠；CDP S7 三語全流程零 raw key。

## Phase 7: Polish & 全量驗收

**Purpose**: 全場景實彈＋全量閘＋final review（收刀簿記另計、不排此）。

- [ ] T024 CDP 七場景全量複跑（quickstart §CDP、**含 S1 兩子步：強制頁錯舊密/違政策拒因顯示＋「登出」鈕退路再登入仍強制**〔analyze G3〕）＋負向自證（拆判定/拆 policy 掛載/拆失敗不計冷卻/拆 getUserInfo 投影 各即紅）＋資料清理（custody 列+測試會員+settings 還原 60）
- [ ] T025 全量閘：容器內 `cargo test -p server -- --test-threads=1`＋`cargo test --test contract --test wire_schema`＋schema-gate 三子命令＋`--self-test`＋typecheck＋`python3 tools/fork-delta-lint`＋`python3 tools/docs-sync check` 全綠
- [ ] T026 final holistic review（雙鏡頭：安全狀態機＋治理合規；只讀不寫、findings 回主線）→ 三分流（修/轉 B-NNN/won't-fix ADR）

**Checkpoint**: 全量閘綠＋final review 零 merge-blocker → finishing（push/merge 需 user 同意）。

---

## 相依圖與並行機會

- **Phase 1**（T001~T003）：不依賴治理 GATE、可先行；T002/T003 [P] 並行（不同檔）。
- **治理 GATE**（憲法 (k)+ADR 0067、主線 AskUserQuestion 親決）→ 起 Phase 2。
- **Phase 2**（T004~T006）BLOCKING：migration→entity→落庫，序列（同表相依）。
- **Phase 3 US1**（MVP）：後端 T007→T008、T009、T010→T011（測試先行）；前端 T012[P]→T013→T014→T015。後端前端可並行推進（不同 worktree）。
- **T014（US1）依賴 T016（US2 浮層元件＋共用 hook）**——定案（analyze I1）：**T016 前移、執行序在 T014 之前**（歸執行單元 U4 首）；Phase 4 其餘掛載點（T017~T019）不被 US1 依賴、照序。
- **Phase 5 US3**：依賴 US1 T008（三寫入路徑就位）——冷卻插既有路徑。
- **Phase 6 US4**：i18n 可與各 US 並行加鍵、但 T022 統一收口＋機器證置後。
- **Phase 7**：全量、序列收尾。

## 執行單元建議切分（Workflow 編排、每單元一支）

1. **U1 工具地基**（T001~T003）：判定 seam＋schema-gate 聯動＋archetype 登記〔治理 GATE 前可跑〕。
2. **[治理 GATE]** 主線 AskUserQuestion 親決憲法 (k)+ADR 0067→accepted+bump→獨立 commit（非 workflow）。
3. **U2 表就位**（T004~T006）：migration＋entity＋落庫＋schema-gate 三綠。
4. **U3 後端首登鏈**（T007~T011）：三寫入＋getUserInfo＋硬閘（含測試先行）。
5. **U4 前端首登鏈**（**T016**＋T012~T015）：浮層元件與共用 hook 先行（T014 顯式前置、analyze I1）→typing＋auth store＋強制頁＋guard。
6. **U5 浮層掛載**（T017~T019）：三掛載點。
7. **U6 冷卻**（T020~T021）：測試先行＋三入口插入。
8. **U7 三語**（T022~T023）：全量鍵＋機器證＋CDP S7。
9. **U8 全量驗收**（T024~T026）：CDP 七場景＋全量閘＋final review。

## MVP 範圍

**US1（Phase 3）＝MVP**：首登強制換密全鏈（經手寫入＋硬閘＋guard＋強制頁＋登出重登）落地即兌現 B-030 核心安全語意；US2 隨機浮層、US3 冷卻、US4 三語為增量。
