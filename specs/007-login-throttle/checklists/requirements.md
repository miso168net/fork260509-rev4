# Specification Quality Checklist: 007-login-throttle 登入失敗節流

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs) — ★**經核可之房規偏離**，見 Notes ①
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders — ★**經核可之房規偏離**，見 Notes ①
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain（**零個**——brainstorm 11 拍板＋對抗式審查已窮盡決策面）
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details) — ★**經核可之房規偏離**，見 Notes ①
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded（FR-021 顯式邊界＋Assumptions 末段「能力已備、觸發遞延」）
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification — ★同 Notes ①

## Validation Log

**Iteration 1（2026-07-10）**——初稿自審，發現並修正 2 處**內部不一致**：

| # | 問題 | 修法 |
|---|---|---|
| 1 | US1 的驗收場景（「窗內失敗 4 次後成功登入」等）在**預設** `captcha_after=2` 下不成立——第 3、4 次失敗其實需通過驗證碼。場景與預設值交互矛盾。 | US1 場景標頭加註「本節場景以**驗證碼停用配置**表述，聚焦節流本身；與驗證碼的交互見 US2」。與 US1 的 Independent Test「本故事在 CAPTCHA 停用配置下即可獨立交付與驗收」對齊。 |
| 2 | US6 場景 2「門檻由 5 改 3 → 連續錯密 3 次 → 第 4 次被鎖」在 `captcha_after=2` 下，第 3 次錯密已需驗證碼——逐次計數的敘述誤導。 | 改寫為「窗內失敗數達 3 → 其後續嘗試即被鎖定；新值於下一次登入判定即生效」，剝除與驗證碼耦合的逐次敘述。 |

另軟化 1 處實作細節：Assumptions 的「測試機制先決」原文直書 `cfg(test)`／`raw SQL`，改為「測試組建限定的故障注入接點」「指定稽核列時間戳的能力」——保留可驗證的**能力要求**，不指定實作手段。

**Iteration 1 結果**：全部項目通過（含 Notes ① 之經核可偏離）。零 `[NEEDS CLARIFICATION]`。**不需 iteration 2**。

## Notes

### ① 三項「實作細節／技術中立」檢查的房規偏離（intentional，非疏漏）

本 repo 的 spec 房規（見 `specs/004-*`／`005-*`／`006-*` 之既有 spec）刻意在 FR/SC 中引用下列技術面，因為它們在本專案中**是契約本身、不是實作選擇**：

- **13 碼矩陣**（`1000`／`2222`／`5000`／`5003`）與 **`msg` i18n key**：憲法 §I.3 明定 base-web 實碼為 wire **唯一權威**、碼矩陣**整組凍結**。寫「回 `2222`＋`auth.login.locked`」是在陳述**不可協商的契約**，改寫成「回一個業務錯誤」反而讓需求不可驗證。
- **端點路徑**（`POST /systemManage/unlockLogin`）：其 casbin 授權於基線 migration 已 seed，路徑是既有事實而非本刀選擇。
- **治理工具與閘門**（gate1／gate2／archetype 歸屬表／`fork-delta-lint`／★軌道／ADR 編號／憲法版本）：屬憲法 §IV Compliance Check 與 §V Governance 的可驗證產出，是本刀的**交付物**。

真正的實作選擇（Redis key 命名、SQL 形狀、模組切分、產圖 crate、advisory lock 與否）**已刻意排除**於 spec 之外，留給 `/speckit-plan`。加密能力（JWT HS256／SHA-256）與新 crate 僅出現在 **Assumptions** 段——該段依模板本就承載「Dependency on existing system/service」。

「Written for non-technical stakeholders」一項：本專案唯一的 stakeholder 即 repo owner（技術決策者），無非技術受眾。

### ② 下一階段的已知前置

- **`/speckit-plan` 的 Constitution Check Q9 必答**：本刀屬「該入憲而未入憲的新行為島」（島 E），須隨本刀排入 MINOR Amendment（v1.3.0 → v1.4.0）；Q2/Q7 亦觸發（★新軌道 `BASE-WEB-LOGIN-CAPTCHA-WIRING`）。
- **依賴釘版待攤案**：唯一新 crate（圖形驗證碼產圖）之版本須於 plan/implement 期雙源查核後由 user 拍板（全域 §6 版本紀律）。
- **測試機制先決**（Assumptions 段第 6 點）：四項守門基建須先建，否則 SC-004／SC-005／SC-008／SC-011 的守門測試會退化成恆綠。此為對抗式審查（testability 鏡頭）揭露的實作期硬前提。

### ③ 來源可信度

本 spec 的每一條 FR 皆可回溯至 `docs/brainstorms/007-login-throttle.md` 的 11 條拍板或其 §0.1 審查修訂（5 blocker／23 major／17 minor）。其中 FR-004（負快取唯一寫入者）、FR-005（鎖中零列）、FR-007（驗證碼零計數）、FR-011 ①②（降級對稱化）、FR-015（白名單精確項）**直接源自對抗式審查抓出的 5 個 blocker**——若無該輪審查，這五條會以錯誤形態進入 spec。
