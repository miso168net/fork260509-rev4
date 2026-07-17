# Implementation Plan: 015-pwd-custody 隨機產密＋密碼經手表＋首登強制換密（B-030 兌現）

**Branch**: `015-pwd-custody` | **Date**: 2026-07-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-pwd-custody/spec.md`

## Summary

B-030 殘餘兌現（隨機生成＋首登強制換密）。核心＝新建**密碼經手表 `sys_pwd_custody`**（複合 PK `(user_id, created_by)`＋`created_at`、零 FK、變體 C）記「誰幫誰設密」；判定規則單一（標的名下存在任一筆 `user_id≠created_by`→首登須換密），三處共用（login 後 getUserInfo 投影／前端 route guard／後端 API 硬閘）。設密三入口（addUser／reset_password／change_own_password）於既有交易＋advisory 鎖內原子寫經手列；**鎖態 token 硬閘**（新 `pwd_gate_mw`、掛 authed＋policy 兩子 router、白名單外 2222 `mustChangePassword`）＋前端全域 guard 攔至 constant route 強制改密頁；改完前端登出重登（後端 changePassword 語意零偏差、ADR 0055 keep-sid 不變式維持）。隨機密碼＝前端 CSPRNG 本地產密浮層（三掛載點）、伺服器回應恆不含密碼。設密冷卻（`password_change_min_interval` settings、預設 60、pair 計、一體適用零例外）。治理＝憲法 MINOR Amendment 新用途 (k)＋ADR 0067 accepted＋Q8 新表（變體 C＋audit 分支聯動）＋Q9 島 I 細項擴充。

## Technical Context

**Language/Version**: Rust stable（rust-api：axum＋sea-orm＋tokio）；TypeScript＋Vue 3（base-web：soybean-admin fork、naive-ui、UnoCSS）

**Primary Dependencies**: 零新依賴（argon2／casbin／sea-orm-migration／vue-i18n／crypto.getRandomValues〔瀏覽器內建〕全既有或平台原生）

**Storage**: PostgreSQL（**新表 sys_pwd_custody＋m011 migration**＋system_settings 新鍵 seed）＋Redis（session denylist／廣播，既有、本刀不動）

**Testing**: cargo test 容器內全程 serial（`docker exec rev4-admin-rust-api-1 sh -c 'cd /app && ...'`）＋contract/wire_schema 契約閘＋schema-gate 三子命令＋vue-tsc typecheck＋`python3 tools/fork-delta-lint`＋CDP 實機七場景（含 token 直打硬閘實彈＋seed 帳號零影響＋冷卻連按）

**Target Platform**: docker compose 自架（dev 五 service）

**Project Type**: web application（rust-api＋base-web 雙 submodule worktree）

**Performance Goals**: 無特定數字目標（admin 面）；硬閘每已認證請求 +1 主鍵 EXISTS 查詢（與 require_policy DB-fresh roles 同向量級、可受）；argon2 verify/hash 全在鎖外／txn 外（沿 014、不佔鎖）

**Constraints**: 零新端點／零新錯誤碼（拒因全 2222 家族 i18n 鍵）／零新 casbin seed（「密碼」動作沿重設密碼按鈕碼）；經手表零 FK（ADR 0009 對齊）；密碼三重不洩（島 I5）；島 I1/I2 合規；fork-delta（guard／auth store／user index.vue 修改型 inline＋新檔圈界）；三語＋Schema 鏡像機器一致；隨機密碼本地 CSPRNG＋回應零密碼

**Scale/Scope**: 1 新表＋1 migration（建表＋1 settings seed）＋facade 3 支加寫入＋1 純函式判定 seam＋getUserInfo additive 加欄＋1 新 middleware（pwd_gate_mw）＋前端 1 產密浮層元件（3 掛載點）＋1 強制改密 constant route 頁＋guard/auth store inline＋i18n 新鍵三語＋schema-gate 工具聯動（audit 分支＋2 白名單＋self-test）

## Constitution Check

*GATE: 對照 constitution v1.13.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（前後端同刀交付）**。無新業務端點；getUserInfo（既有 `/auth/getUserInfo`）additive 加 `needChangePwd`；硬閘＝middleware 對既有端點加閘；設密經手寫入在既有 addUser／reset_password／changePassword 端點內。前端消費面（guard 判定、浮層、強制頁）與後端投影／閘同刀、無先後斷差。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、需新用途 (k) MINOR Amendment**。修改型 inline（帶 `原行:`）＝①`router/guard/route.ts` 全域強制改密攔截②`store/modules/auth/*` needChangePwd 承載（optional 欄免補初值）③`views/manage/user/index.vue` operate 欄「密碼」動作④`views/manage/user/modules/user-operate-drawer.vue` add 密碼欄旁隨機鈕⑤`views/user-center/modules/password-card.vue` 隨機鈕（(g) 射程確認）⑥locale 三檔＋app.d.ts i18n（圈界）。新增型圈界＝產密浮層元件／強制改密頁 constant route／`rev4-*.d.ts` needChangePwd declaration merging／constantRoutes 名單一行。**十用途 (a)~(j) 無一涵蓋強制改密頁＋route guard 攔截控制流＋auth store**→新用途 **(k)** MINOR Amendment（含「＋對應 i18n key」字樣自始寫入、(a)/(h)/(g) 擴字面併敘）。 |
| Q3 | menu 顯示走 Casbin enforce？ | **是、零新 casbin**。強制改密頁＝constant route（靜態併集免曝光鏈、非 Casbin menu、hideInMenu）；operate 欄「密碼」動作沿用既有「重設密碼」按鈕碼（clarify Q2 親決）→ casbin p 列與 sys_menu.buttons 零改動；§I.2 選單顯示語意不觸發。 |
| Q4 | wire 對齊 §I.3 權威序與不變式？ | **是**。envelope `{data,code,msg}` 凍結不動；**零新 route→registry 筆數不變、無新 contract case**；getUserInfo 回應 additive 加 `needChangePwd:boolean`（UserInfo DTO——rev4 首例對凍結 `Api.Auth.UserInfo` interface 成員級 declaration merging；contract/wire_schema 現無 UserInfo 形狀斷言、additive 安全、補正負向新斷言）；拒因全 **2222**＋msg=i18n key（`biz.auth.mustChangePassword`／`biz.user.pwdSetTooFrequent`，零新碼）；`typings/api/auth.d.ts` 憲法凍結不動（走 net-new ADAPT `.d.ts`）。 |
| Q5 | 從前代 source 拷貝 code？ | **否**。rev3 純綠地（K2-14/F-7 停在候選、無 as-built）；password-card 政策 rules 邏輯抽共用 hook＝rev4 014 as-built 內重排（非 rev3 拷貝）。 |
| Q6 | 抵觸 §II 拍板？ | **否**。dynamic route／unknown header／`/api` 前綴皆照現制消費、不涉。 |
| Q7 | 觸及 §III ★ 軌道？「補完」還是「新能力」？ | **是＝新能力（新用途 (k)）**。強制改密頁＋route guard 攔截控制流＋auth store inline＝現行十用途無涵蓋→MINOR Amendment 新用途 (k)（§V.3「軌道授權邊界擴展（新用途）」；判準＝控制流層新頁與攔截、非既有款字面縫隙）。**★不做 axios 攔截器兜底**（憲法 :204/224/236 三處攔截器控制流禁令維持；「admin 重設活躍 session」由既有 8888 撤銷管線覆蓋）。manage「密碼」動作與浮層＝(a)/(h) 擴字面併入 (k) 枚舉敘明；user-center 改密卡隨機鈕＝(g) 射程確認。順帶勘誤憲法「九用途／十用途」紀律行失步（v1.13.0 加 (j) 遺留）。 |
| Q8 | 新建業務表（create migration）？§I.6 六審計欄？ | **是＝變體 C 新表**。`sys_pwd_custody`＝複合 PK `(user_id, created_by)`＋`created_at timestamptz NOT NULL default now()`；零 FK（ADR 0009 對齊）、硬刪、不存密碼、無 `updated_*`/`deleted_*`。歸屬變體 C（狀態記錄、非 archetype 六審計欄）。**工具聯動（m011 同 commit、缺一即紅）**：archetype-map.json 登記（variant C、note 記 created_at＝最後設定時間語意）＋data-model §1 歸屬補列＋schema-gate STRUCT_ADDITIVE_ALLOWLIST（表級、ADR 0039）＋**audit_table 加 `sys_pwd_custody` 專屬分支**（現行變體 C 僅 sys_user_role／sys_token 硬編碼、schema-gate:585/589、else 即 FAIL）＋TestAuditTable 案例＋SEED_ADDITIVE_ALLOWLIST（`password_change_min_interval` settings 鍵）＋self-test dict 同步。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是＝島 I 新細項擴充（傾向、隨刀 MINOR Amendment）、零新獨立島**。**島 I1**：設密三入口（addUser 豁免鎖＝新列 commit 前不可見；reset_password／change_own_password 既有 advisory_lock_user_db）內原子寫經手列。**島 I2**：改密撤 session keep-sid 語意零偏差（登出由前端於成功後另發、非後端撤本 sid）＝ADR 0055 不變式維持；★硬閘每請求 EXISTS 判定 MUST 論證與島 I2「MUST NOT 為此新增每請求活性判定」的射程區隔——該禁令限**撤銷即時性**（session 活性），custody 閘＝改密強制、不在射程。**島 I5**：密碼驗證複用單一驗證點零分叉（冷卻＝端點固有規則、排既有拒因後、MUST NOT 入驗證點）；經手表結構性零密碼欄；隨機密碼本地生成＋回應零密碼＝零新洩漏面。判定規則／寫入規則／冷卻／硬閘白名單語意＝島 I 新細項、Q9 隨刀 Amendment。 |

**Gate 結論**：**通過**。需 **user 親決**（治理路徑、非違規）＝①**憲法 MINOR Amendment 新用途 (k)**（v1.13.0→v1.14.0；含 (a)/(g)/(h) 擴字面併敘＋「＋對應 i18n key」＋九/十用途失步勘誤）②**ADR 0067 draft→accepted**（經手表模型＋鎖態 token 硬閘選型）。親決時點照 013/014 判例＝analyze 後一併、最遲於前端 guard 單元與 migration 單元之前；程序照 §V.2（改 constitution.md＋bump＋獨立 commit `docs(constitution): amend`＋ADR 同批轉 accepted＋docs-sync generate）。Q9 島 I 細項擴充字面隨本 Amendment 併入。

**Phase 1 後複查（research/data-model/contracts/quickstart 產出後）**：九題判定**全維持**——設計產物未引入新端點／新錯誤碼／新依賴／新獨立行為島；Q4 getUserInfo additive 加欄與零新 route 已定稿於 contracts/；Q8 之 sys_pwd_custody DDL＋工具聯動已落 data-model §1/§2＋contracts/；Q9 之島 I1/I2/I5 合規（設密寫入鎖內原子、硬閘射程區隔論證、經手表零密碼）已落 data-model §3 狀態機；Q2/Q7 之 (k) Amendment 字面已定（research R-GOV）。

## Project Structure

### Documentation (this feature)

```text
specs/015-pwd-custody/
├── plan.md              # 本檔
├── research.md          # Phase 0（R-* 定案：判定規則／硬閘掛點／冷卻位置／隨機生成／治理路徑／rev3 綠地）
├── data-model.md        # Phase 1（sys_pwd_custody DDL＋工具聯動＋設密狀態機固定序＋getUserInfo DTO 加欄）
├── quickstart.md        # Phase 1（全量閘＋CDP 七場景＋負向自證）
├── contracts/
│   └── pwd-custody-contracts.md   # Phase 1（getUserInfo wire 變更＋硬閘白名單＋settings 新鍵＋i18n 鍵清單）
├── checklists/requirements.md     # specify 產（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產、非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 build/test、單一 cargo 進程 serial）
├── migration/src/m011_pwd_custody.rs           # 新：建 sys_pwd_custody 表＋seed password_change_min_interval（照 m004/m009 DDL+seed 複合先例）
├── migration/src/lib.rs                         # 動：Migrator 陣列註冊 m011
├── entity/src/sys_pwd_custody.rs                # 新：entity Model（複合 PK、零 FK relation）
├── entity/src/（lib/mod）                        # 動：mod sys_pwd_custody
├── server/src/model/facade/sys_user.rs          # 動：insert／reset_password／change_own_password 各加經手列寫入＋冷卻檢查＋判定 seam（純函式 need_change_pwd）
├── server/src/handler/auth.rs                   # 動：get_user_info 加 needChangePwd EXISTS 查詢＋UserInfo struct 加欄＋正負向斷言
├── server/src/middleware/（pwd_gate）            # 新：pwd_gate_mw（判定真→白名單 path 外 2222 mustChangePassword）
├── server/src/router.rs                         # 動：build() authed＋policy 兩子 router 掛 pwd_gate_mw（enforce 後、access_log 內側）
├── server/tests/contract.rs                     # 動：getUserInfo needChangePwd 斷言（registry 筆數不變）
└── server/tests/*（新測）                        # 判定三態／三寫入路徑／冷卻正負向／硬閘白名單內外

tools/schema-gate                                # 動：audit_table +sys_pwd_custody 分支＋TestAuditTable 案例＋STRUCT_ADDITIVE_ALLOWLIST＋SEED_ADDITIVE_ALLOWLIST＋self-test dict
docs/ops/reference-src/archetype-map.json        # 動：sys_pwd_custody 登記（variant C）
specs/002-schema-baseline/data-model.md          # 動：§1 表歸屬補列（audit 守門來源）

base-web/（worktree；fork-delta 紀律）
├── src/components/（新）產密浮層元件            # 新：產生/顯示切換/複製/帶入、CSPRNG、構造性合政策
├── src/views/_builtin/（新）force-change-pwd    # 新：強制改密 constant route 頁（舊密+新密+確認+隨機鈕+登出鈕）
├── src/views/manage/user/index.vue                        # 動：operate 欄「密碼」動作（修改型 inline、原行標）
├── src/views/manage/user/modules/user-operate-drawer.vue # 動：add 密碼欄旁隨機鈕（修改型 inline）
├── src/views/user-center/modules/password-card.vue        # 動：儲存前隨機鈕＋buildPolicyRules 抽共用 hook（(g) 射程）
├── src/router/guard/route.ts                              # 動：全域 needChangePwd 攔截（修改型 inline、原行標、置於路由存在性解析之先）
├── src/store/modules/auth/*                                # 動：needChangePwd 承載（optional、修改型 inline）
├── src/typings/api/（新）rev4-pwd-custody.d.ts             # 新：Api.Auth.UserInfo needChangePwd declaration merging
├── build/plugins/router.ts                                # 動：constantRoutes 名單 +force-change-pwd（修改型 inline）
├── src/locales/langs/{zh-tw,zh-cn,en-us}.ts               # 動：浮層/強制頁/拒因/settings 標籤新鍵（圈界）
└── src/typings/app.d.ts                                   # 動：App.I18n.Schema 鏡像（圈界）

.specify/memory/constitution.md                  # 動（親決後）：§III.2 新用途 (k)＋version v1.14.0＋九/十用途勘誤
docs/arc42/decisions/0067-*.md                   # 動（親決後）：draft→accepted
```

**Structure Decision**: 後端＝新 migration＋新 entity＋facade 就地加寫入（三入口同點）＋新 middleware（pwd_gate_mw 掛既有 build() 疊放縫）＋getUserInfo 就地加欄；判定規則收斂為單一純函式 seam（三處呼叫、防分叉）。前端＝產密浮層新元件（一支三掛載）＋強制改密頁新 constant route（比照 login 系 _builtin）＋guard／auth store／manage index 修改型 inline。治理重心＝新用途 (k) Amendment＋ADR 0067＋新表 Q8 工具聯動（audit 分支必補、否則 gate 紅）。

## Complexity Tracking

> 無 Constitution Check 違規——新用途 (k) Amendment 與 ADR 0067 均為治理正名路徑（親決 GATE），非違規繞道；新表走變體 C 既有軌道；本表空置。
