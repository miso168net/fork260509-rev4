# Implementation Plan: 014-user-center 個人中心自助頁（B-090 自助改密兌現＋rev3 025 全頁承襲）

**Branch**: `014-user-center` | **Date**: 2026-07-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-user-center/spec.md`

## Summary

任何登入者可用的個人中心自助頁：UI 逐項承襲 rev3 025 成品（單欄四卡：修改密碼→信箱→手機號→基本資料、驗證碼佔位三處），後端新建 auth-only 4 端點家族 `/userCenter/*`（`Protection::Authed`、operator=claims.uid）。主刀口＝自助改密固定驗證序（帳號存在→confirm 一致→舊密正確→新≠舊→政策）＋rev4 補撤 session（keep-sid、島 I2/I5 合規時序：鎖外 verify/hash、鎖內 phc 純比對）；選單可達性走 getUserRoutes 恆附掛 self-service 白名單（ADR 0065）。零 migration、零 schema 變更、零新錯誤碼、零新依賴、零 casbin seed。

## Technical Context

**Language/Version**: Rust stable（rust-api：axum＋sea-orm＋tokio）；TypeScript＋Vue 3（base-web：soybean-admin fork、naive-ui、UnoCSS）

**Primary Dependencies**: 零新依賴（argon2／casbin／vue-i18n 全既有）

**Storage**: PostgreSQL（既有 schema、**零 migration**）＋Redis（session denylist／廣播、既有）

**Testing**: cargo test 容器內全程 serial（`docker exec rev4-admin-rust-api-1`）＋contract/wire_schema 契約閘＋vue-tsc typecheck＋`python3 tools/fork-delta-lint`＋CDP 實機驗收（三語＋非-super 帳號＋keep-sid 雙 session）

**Target Platform**: docker compose 自架（dev 五 service）

**Project Type**: web application（rust-api＋base-web 雙 submodule worktree）

**Performance Goals**: 無特定數字目標（admin 自助頁）；argon2 verify/hash 全在鎖外與 txn 外計算（不佔鎖、不拉長交易）

**Constraints**: UI 與 rev3 逐項一致（user 拍板硬約束）；零 migration／零新錯誤碼（全 2222）／零新依賴；島 I1/I2/I5 合規；fork-delta（index.vue 修改型 inline＋新檔圈界）；三語＋Schema 鏡像機器一致

**Scale/Scope**: 單頁 4 卡＋4 新端點＋facade 3 支新建＋getUserRoutes 白名單附掛＋i18n 29 承襲鍵×3 語＋3 新拒因鍵×3 語＋1 成功 toast 鍵×3 語

## Constitution Check

*GATE: 對照 constitution v1.11.0 §IV 九題逐項 yes/no。Phase 1 後複查。*

| # | 題 | 判定 |
|---|---|---|
| Q1 | 違反 §I.1 base-web 為權威？rust-api 未提供 base-web 用到的端點？ | **否（前後端同刀交付）**。`/userCenter/{getProfile,updateProfile,getPasswordPolicy,changePassword}` 4 端點全新建（rev4 首個 auth-only 業務端點家族）；契約以 rev3 as-built 為藍本隨刀定稿（camelCase wire、`Res<T>` 信封）；前端消費面與端點面同刀、無先後斷差。 |
| Q2 | 動 base-web inline？屬 §III.2 哪個用途？授權邊界內？依 fork-delta 紀律？ | **是、頁本體落 (g) 既有用途，i18n 一處須隨刀 Amendment**：①`views/user-center/index.vue` 改寫＋`modules/*` 4 卡＝MODAL-WIRING **(g)**「非-manage 頂層自助頁」字面**全涵蓋**（profile 自助檢視／編輯＋改密＋驗證 UI 佔位、auth-only 端點、hideInMenu:true）——零新用途款；②**page.userCenter.\* 29 鍵三語＋App.I18n.Schema 鏡像＝(g) 擴字串 Amendment 候選**（(g) 字面不含「＋對應 i18n key」、(c)(d)(e)(h)(i) 五用途全明寫對照顯著；MINOR、照 v1.11.0 (d) 擴字串前例）；③WRAPPER/ADAPT（`rev4-user-center.ts`／`rev4-user-center.d.ts`）＝§III.1 新檔零原行；④index.vue＝**修改型 inline**（基線 7 行 LookForward 佔位頁、`原行:` 逐字標）；⑤locale 三檔＋app.d.ts 增量走 `rev4-inline` 圈界；⑥`backend.biz.user.*` 新拒因鍵（oldPasswordMismatch／passwordMismatch／passwordSameAsOld）＝I18N-WIRING **(ii)(iii)** 既有 backend 命名空間資料級補完。 |
| Q3 | menu 顯示走 Casbin enforce？ | **是、含一筆憲法內頁級豁免**。user-center＝(g) 明文「`hideInMenu:true`、經頭像下拉入口、非 Casbin menu」——此頁不顯示於選單、§I.2「有權才顯示」的選單顯示語意不觸發；**路由可達性**走 getUserRoutes 恆附掛 self-service 白名單（ADR 0065：casbin 過濾結果之後聯集、業務 menu 的 Casbin 過濾零改動、白名單擴充紀律鎖死 RBAC 資源頁禁入）；既存 `p|R_SUPER|user-center|menu` 列保留（聯集下冗餘無害、硬刪屬 B-060 seed 移除軌道）。 |
| Q4 | wire 對齊 §I.3 權威序與不變式？ | **是**。envelope `{data,code,msg}` 凍結形不動；**4 新 route→registry +4＋contract case 4 筆**（get-profile／update-profile／get-password-policy／change-password、`Protection::Authed`、缺 case 即紅）；拒因全 **2222**＋msg=i18n key（政策違規沿 011 `BizData("biz.user.passwordPolicy", violations)` 明細形＋`passwordViolation.*` 8 鍵三語已備；舊密不符／兩次不一致／新同舊三鍵新增於 biz.user.* 域）；id i64→JSON number 2^53 守衛；時間 RFC3339 帶 offset；getProfile 回應**零密碼零會話識別**（島 I5 三重不洩）。 |
| Q5 | 從前代 source 拷貝 code？ | **否**。rev3 025 為受控參照不拷貝（§I.5）；承襲結論清單載 brainstorm §0.1（含 rev3 已知坑防重踩：confirm rule toRef／radio 切換清憑證／F-6 並發假報修形／F-2 ORDER BY）；**不可照抄四處明列**：①update_own_profile 須島 I1 advisory lock（rev3 無鎖）②changePassword 時序須島 I5 合規（rev3 無此約束；鎖外 verify/hash、鎖內 phc 純比對）③user_gender 走 rev4 `wire_enum12` 形（rev3 裸 i16 繞過 rev4 wire 不變式）④錯誤鍵落 rev4 `biz.user.*` 域（rev3 為 biz.password.* 域＋notFound 鍵名不同）。 |
| Q6 | 抵觸 §II 拍板？ | **否**。#1 unknown header／#2 dynamic route／#3 `/api` 前綴皆照現制消費、不涉。 |
| Q7 | 觸及 §III ★ 軌道？「補完」還是「新能力」？ | **是**。MODAL-WIRING：頁本體＝**(g) 授權邊界內**（字面逐項核實全涵蓋——本刀即 (g) 的首次兌現）；**page.userCenter.\* i18n key＝軌道授權邊界擴展（擴 (g) 既有款字串「＋對應 i18n key」）→ MINOR Amendment**（判準：(g) 授權頁面本體、五平行用途皆明寫 i18n 而 (g) 獨缺＝字面縫隙非新能力，但依 013 判例字面縫隙以擴字串正名、不走寬讀）；I18N-WIRING (ii)(iii)＝既有 backend 命名空間**資料級補完**（ADR 0041 釋義射程內、零新 top-level 命名空間）；getUserRoutes 白名單附掛＝**後端 handler 改動、非 base-web fork-delta ★軌道面**（治理歸 ADR 0065＋§I.2/§III.2(g) 調和、見 Q3）。LOGIN-CAPTCHA／LOGOUT-UX／AUTH-／DEVPROXY-WIRING 不涉。 |
| Q8 | 新建業務表（create migration）？§I.6 六審計欄？ | **否——本刀零 migration**（比 013 更乾淨：m 系列零新增）。sys_user／system_settings／sys_token／session_event 全既有；**schema-gate 三閘全不觸**（零結構變更、零 seed 變更——白名單案免 casbin seed 正是 D1 的收益之一）；gate2 244/244 預期不變。 |
| Q9 | 觸及 §I.7 行為島？invariants 保持？新島進場？ | **是（全數保持、零新島）**。**島 I1**：change_own_password／update_own_profile＝「以既有使用者為標的之使用者域寫端」→交易起手 advisory_lock_user_db（與 login/refresh 共鎖）＋lock-then-redecide（照 011 update／reset_password 範式）。**島 I2**：改密撤 session＝同交易（業務寫＋token 作廢＋session_event 同 commit）→權威優先→廣播 best-effort（殘留窗上界＝憲法明文接受）；keep-sid＝ADR 0055 不變式「保留當前操作 session」的操作者=標的釋義（★該釋義已隨 v1.12.0 入憲——島 I2 改密句補釋義字面、analyze C1 收口；ADR 0053 偏差句以 0055 為準、版本史載明）；`revoked`/8888 靜默類、不與 `kicked`/7777 互換。**島 I5**：密碼政策驗證複用單一驗證點零分叉（★「新≠舊」規則＝改密端點固有規則、明文比對、**MUST NOT 入單一驗證點**——建帳/管理員重設無舊密可比、入點即分叉）；密碼三重不洩（ChangePwdReq Debug 遮蔽照 ResetUserPasswordReq 範式、op-log payload 白名單 {id, user_name} 零密碼、getProfile 回應零密碼零會話識別）；**雜湊與 verify 全在鎖外／txn 外計算**（「密碼雜湊 MUST NOT 於持有列鎖期間計算」）。**島 C**：8888 登出碼既有管線消費、不改語意。★零新行為島——自助域＝島 I 既有範圍的操作者=標的變體。 |

**Gate 結論**：**通過**。需 **user 親決**（治理路徑、非違規）＝①**MODAL-WIRING (g) 擴字串**「＋對應 i18n key」（MINOR **v1.11.0→v1.12.0**）②**ADR 0065 draft→accepted**（getUserRoutes 恆附掛 self-service 白名單）。親決時點照 013 判例＝analyze 後一併、最遲於**前端 i18n 單元與 getUserRoutes 單元之前**；程序照 §V.2（改 constitution.md＋bump＋獨立 commit `docs(constitution): amend`＋ADR 同批轉 accepted＋docs-sync generate）。

**Phase 1 後複查（research/data-model/contracts/quickstart 產出後）**：九題判定**全維持**——設計產物未引入新表／新錯誤碼／新依賴／新憲法島；Q4 registry +4 與 contract case 4 筆已逐端點定稿於 contracts/；Q9 之島 I1/I2/I5 合規時序已落 data-model §4 固定序（鎖外 verify/hash→txn 鎖內 phc 比對→撤 session→op-log→commit→廣播）；Q2/Q7 之 amendment 候選字面已定（見 research R8）。

## Project Structure

### Documentation (this feature)

```text
specs/014-user-center/
├── plan.md              # 本檔
├── research.md          # Phase 0（R1~R9：接地定案＋rev3 承襲/不可照抄清單）
├── data-model.md        # Phase 1（零 schema 變更聲明＋4 端點 DTO 逐欄＋改密固定序狀態轉移）
├── quickstart.md        # Phase 1（全量閘＋CDP 驗收場景含非-super＋keep-sid 雙 session＋負向自證）
├── contracts/
│   └── user-center-endpoints.md   # Phase 1（4 端點契約＋拒因鍵＋registry/case 對帳＋fetcher 對帳）
├── checklists/requirements.md     # specify 產（16/16）
└── tasks.md             # Phase 2（/speckit-tasks 產、非本命令）
```

### Source Code (repository root)

```text
rust-api/（worktree；容器內 build/test、單一 cargo 進程 serial）
├── server/src/handler/user_center.rs          # 新：4 端點 handler（固定驗證序＋DTO＋Debug 遮蔽）
├── server/src/handler/mod.rs                  # 動：mod user_center
├── server/src/handler/route.rs                # 動：get_user_routes 白名單附掛（SELF_SERVICE_ROUTES 常數）＋resolve_home 交互測試擴充
├── server/src/model/facade/sys_user.rs        # 動：get_own_profile／update_own_profile／change_own_password 三支新建（島 I1 鎖＋窄寫＋op-log redact）
├── server/src/model/password.rs               # 動：政策 7 鍵常數 pub 化（getPasswordPolicy allowlist 同源、防字面漂移）
├── server/src/router.rs                       # 動：ROUTES +4 筆（Protection::Authed＋case_key）
└── server/tests/contract.rs                   # 動：4 新 case 結構斷言（registry 筆數 +4）

base-web/（worktree；fork-delta 紀律）
├── src/views/user-center/index.vue                       # 動：基線 7 行佔位頁改寫（修改型 inline、原行逐字標）——canonical ProfileModel＋4 卡組裝
├── src/views/user-center/modules/password-card.vue       # 新：改密卡（radio 三選＋政策動態規則＋toRef confirm＋新≠舊即時提示）
├── src/views/user-center/modules/email-card.vue          # 新：信箱卡（值輸入＋驗證碼佔位組）
├── src/views/user-center/modules/phone-card.vue          # 新：手機卡（同構）
├── src/views/user-center/modules/basic-info-card.vue     # 新：基本資料卡（唯讀欄＋暱稱/性別編輯）
├── src/service/api/rev4-user-center.ts        # 新：WRAPPER 4 fetcher（直接路徑 import 不經 barrel）
├── src/typings/api/rev4-user-center.d.ts      # 新：ADAPT declaration merging（Api.UserCenter.*）
├── src/locales/langs/{zh-tw,zh-cn,en-us}.ts   # 動：page.userCenter.* 29 鍵＋backend.biz.user.* 3 新鍵（圈界）
└── src/typings/app.d.ts                       # 動：App.I18n.Schema 鏡像（圈界）

.specify/memory/constitution.md                # 動（親決後）：§III.2 (g) 擴字串＋version v1.12.0
docs/arc42/decisions/0065-*.md                 # 動（親決後）：draft→accepted
```

**Structure Decision**: 後端一新 handler 檔（照 012 audit 先例——全新端點家族開新檔、異於 013 之就地擴）＋facade 就地加三支；前端 index.vue 為 rev4 首個「基線佔位頁改寫」修改型標的、modules 全新檔；零 migration 零 schema-gate 觸動＝治理面最輕的一刀（治理重心在 amendment 親決與 ADR 0065）。

## Complexity Tracking

> 無 Constitution Check 違規——(g) 擴字串與 ADR 0065 均為治理正名路徑（親決 GATE），非違規繞道；本表空置。
