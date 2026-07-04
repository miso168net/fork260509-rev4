# Implementation Plan: 004-system-settings 系統設定縱切（首個 facade/授權層＋base-web 首刀）

**Branch**: `004-system-settings` | **Date**: 2026-07-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-system-settings/spec.md`；上游＝
`docs/brainstorms/004-system-settings.md`（七題拍板）、ADR 0008／0026／0027／**0028**（本刀
plan 立的 i18n 軌道 Amendment）、constitution v1.1.0 §I.2/§I.3/§I.5/§I.6/§III。clarify 1 題
已入 spec（zh-TW＝全字典全量對等）。

## Summary

在 server 內建**首個** facade→handler→授權→wire 分層（rev3 結構參照、§I.5 全新寫）：
`system_settings` facade（entity 存取唯一管道、`entity_access_lint` 首建）＋型別驗證 registry
（ADR 0026：per-key 範圍＋正規化＋未知型拒）＋最小授權骨架（ADR 0027：`enforce_mw` JWT-decode
＋`require_policy` casbin DB-fresh roles、登入延 auth 刀）＋同 txn op-log（§I.6）＋兩端點
（getSystemSettings／updateSystemSetting、super-only）；掛入 US3 覆蓋閘、刪 demo（B-056）。
前端（base-web 首刀）：typings（ADAPT）＋service（WRAPPER）＋KV 設定頁（★MODAL-WIRING (e)）＋
i18n 接線（★(i)~(iii)）＋**完整 zh-tw locale**（★(iv)/ADR 0028：全字典 ~515 鍵＋6 inline 註冊
＋語言選單繁體＋預設 zh-TW）；前端守門＝vue-tsc typecheck＋lint＋locale 對等 lint（無 vitest、
拍板 B）。技術路徑沿已驗證形：後端結構參照 rev3、前端 locale 機制經 plan 實測定案。

## Technical Context

**Language/Version**: Rust 1.96.1（沿 001；rust-toolchain 已釘）；前端 Vue 3＋TypeScript
（vue-tsc typecheck）＋naive-ui；locale＝vue-i18n（inline 註冊）。

**Primary Dependencies**: 新增後端 jsonwebtoken 9（JWT decode、HS256；MSRV pin 見 research R2）
＋casbin 2.20.0（enforce、adapter＝已 vendored sea-orm-adapter）＋metrics 0.23（casbin counter）；
sea-orm 1.1.20／serde 已在 workspace。熱套用 documented-stub→redis **暫不加**（R6）。前端零新
runtime 依賴（不引 vitest；naive-ui `zhTW`/`dateZhTW`、dayjs `zh-tw` 已在上游）。

**Storage**: 002 baseline（system_settings 8 seed＋casbin R_SUPER policy＋sys_menu 條目）；
本刀零 migration／零 seed 改動。

**Testing**: 後端容器內 `cargo test --workspace`（型別 registry／facade op-log／authz 注入身分／
contract case／覆蓋閘／entity_access_lint）＋命令級驗收（quickstart：curl 注入 token）。前端
`pnpm gen-route && typecheck`（vue-tsc 型閘門）＋`lint`＋locale 對等 lint（無 runtime 單元測試、拍板 B）。

**Target Platform**: 001 dev stack（WSL2 Docker Compose）；host 零工具鏈。

**Project Type**: web（rust-api 後端縱切＋base-web 前端首刀）；雙倉——後端住 rust-api worktree、
前端住 base-web worktree（各兩段式 commit＋pin bump）。

**Performance Goals**: 不破 001 啟停時效；設定端點低頻（super-only、8 列）、無效能標的。

**Constraints**: rust build/test 全程容器內 serial；base-web 改動限授權軌道（★(e)/(i)~(iv)/ADAPT/
WRAPPER）＋fork-delta `rev4-inline` 標記；前端 live 走查需 auth（拍板 7、留 auth 刀）；交付碼
零前代代號（FR-015）；JWT sign/登入不在本刀。

**Scale/Scope**: 後端 4 新面（facade／validation registry／auth seam／handler）＋2 端點＋op-log
接地；前端 typings＋service＋1 頁＋i18n 接線＋**全 zh-tw 字典（~515 鍵繁化）**＋6 inline 註冊；
守門 5 類（型驗/op-log/authz/覆蓋閘/entity_access_lint）＋前端 3 lint。

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.* 對照 constitution
**v1.1.0** §IV 九題：

| # | 檢查 | 結果 | 依據 |
|---|---|---|---|
| 1 | 違反 §I.1 base-web 權威／未供 endpoint？ | **No** | 本刀供 base-web 設定頁所需 getSystemSettings/updateSystemSetting；能力面不縮減 |
| 2 | 動 base-web inline？屬 §III.2 哪範圍？fork-delta？ | **Yes——授權內** | ★(e) 設定頁（拍板 3、spec 記依據）＋★(i) 攔截器 msg→$t＋★(iv) 全 zh-tw locale/註冊（ADR 0028、v1.1.0 授權）；ADAPT/WRAPPER 走新檔；全走 rev4-inline 紀律 |
| 3 | menu 顯示走 Casbin enforce？ | **Yes/N-A** | sys_menu `manage_system-settings` 已 seed（002）；現 static 模式 route+roles meta 過濾；dynamic（casbin menu）隨 auth 刀。無新 seed |
| 4 | wire 對齊 §I.3？ | **Yes** | 統一信封 Res／13 碼（2222 Biz／5003／0000）／msg=key（biz.systemSettings.*）／settingType 字串 id 型；無 mock |
| 5 | 前代 source 拷貝？§I.5 例外？防回歸？ | **No（受控參照）** | rev3 facade/validate/handler/auth 為結構參照、全新寫；防回歸：enforce_mw 不帶 session/denylist（屬 auth 刀）、JWT sign 不帶 |
| 6 | 抵觸 §II 拍板？ | **No** | 端點走 /systemManage/*（後端形；front-nginx strip /api）；#1/#2/#3 不涉 |
| 7 | 觸及 §III ★ 軌道？授權內？補完 vs 新能力？ | **Yes——經 Amendment 授權** | ★(e)/(i)~(iii) 授權內；★全 zh-tw locale 原逾 (ii)＝新能力→**ADR 0028 立 (iv)、constitution v1.1.0**（本刀 plan 期立、user 拍板；已 commit）→現授權內 |
| 8 | 新建業務表？§I.6 審計欄？ | **No** | 零 migration；system_settings 002 已建含審計六欄；本刀 update 走 §I.6 成對寫＋同 txn op-log |
| 9 | 觸及 §I.7 行為島？ | **No** | §I.7 空；設定 CRUD 無狀態機（single_session 消費屬 auth/session 刀） |

**GATE 通過**（Q7 經 ADR 0028 Amendment 解除；Complexity Tracking 記 zh-tw 範圍擴大）。

## Project Structure

### Documentation (this feature)

```text
specs/004-system-settings/
├── plan.md              # 本檔
├── research.md          # Phase 0：rev3 結構接地＋前端 locale 實測＋釘版＋Amendment＋B-009 審
├── data-model.md        # Phase 1：wire/型驗 registry/授權/audit/前端 形定稿
├── quickstart.md        # Phase 1：命令級驗證（curl 注入 token／cargo test／typecheck+lint）
├── contracts/
│   ├── settings-api.md       # 後端 API＋型驗＋授權比對規則
│   └── frontend-track.md     # 前端軌道歸屬＋i18n＋守門契約
└── tasks.md             # Phase 2（/speckit-tasks、非本命令）
```

### Source Code (repository root)

```text
# rust-api worktree（rev4-admin-rust-api）
rust-api/server/src/
├── model/facade/system_settings.rs   # 首個 facade（entity 存取唯一管道）
├── model/audit.rs                     # op-log seam（mutate_in_txn／AuditEvent）
├── model/facade/sys_operation_log.rs  # op-log 落庫（entity_id=None for KV）
├── auth/{mod,jwt,enforce}.rs          # 授權骨架（Claims decode／require_policy casbin）
├── handler/system_settings.rs         # 兩端點＋型別驗證 registry（或 validation 子模組）
├── state.rs                           # AppState（db/jwt/enforcer）
├── router.rs／lib.rs／main.rs         # 端點掛入＋刪 demo（B-056）
└── tests/                             # 型驗/op-log/authz/contract/覆蓋閘/entity_access_lint

# base-web worktree（rev4-admin-base-web）——全走 rev4-inline fork-delta
src/typings/api/rev4-system-settings.d.ts    # ADAPT 新檔
src/service/api/rev4-system-settings.ts      # WRAPPER 新檔
src/views/manage/system-settings/index.vue   # ★(e) 頁（route regen）
src/service/request/index.ts                 # ★(i) msg→$t（L71/109 inline）
src/locales/langs/{zh-cn,en-us,zh-tw}.ts     # ★(ii) backend 命名空間；★(iv) zh-tw 全字典新檔
src/locales/{locale,naive,dayjs,index}.ts    # ★(iv) 註冊 inline
src/store/modules/app/index.ts               # ★(iv) localeOptions 繁體＋預設
src/typings/app.d.ts                         # ★(iii) Schema＋★(iv) LangType
```

**Structure Decision**: 雙倉分工——後端住 rust-api worktree（首建 facade/model/auth 層、
兩段式 commit＋pin bump）；前端住 base-web worktree（base-web 首刀、軌道授權內、兩段式 commit
＋pin bump）。信封/錯誤沿 003；授權骨架/facade/audit 結構參照 rev3、全新寫。

## Complexity Tracking

| 事項 | 為何需要 | 為何未選更簡替代 |
|---|---|---|
| 全 zh-tw locale（~515 鍵）＋constitution Amendment (iv) | user clarify 拍板全字典 zh-tw primary UI；ARCHITECTURE §8 本就宣稱 zh-TW primary＋語言選單繁體 | 更簡替代＝限 backend 命名空間（無 Amendment）；user 明示採納較重範圍以早得完整 zh-tw UI |
| jsonwebtoken/casbin 授權骨架先於登入 | ADR 0008 要第一刀打通授權；casbin policy 已 seed | 授權留白＝管線少驗一環（ADR 0027 否決）；登入拉進＝blast radius 過大 |

## 憲法 Post-Design Re-Check（Phase 1 之後）

Phase 1 產物（data-model／contracts／quickstart）未引入新軌道觸碰、業務表或前代拷貝；§IV
Q2/Q7 的 zh-tw 面已由 **ADR 0028 Amendment（v1.1.0）** 授權（本刀 plan 期立、已 commit）；
Q5 受控參照範圍未擴（結構參照、零整檔拷貝、防回歸帶入）——**GATE 維持通過**。

備註：核心 plan 的「update agent context」步驟 rev4 明示跳過（agent-context extension 未安裝、
沿 001/002/003 先例）；技術上下文由本 plan＋brainstorm＋research 承載。
