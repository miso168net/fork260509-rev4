# Specification Quality Checklist: 008-ip-gate IP 存取控制閘＋信任錨基建

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-10
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit-clarify` or `/speckit-plan`

### 驗證判讀（2026-07-10，首輪）

- **實作細節洩漏**：spec 全程以能力語言撰寫，未提任何語言／框架／具體資料表名／欄名／函式名／API 路徑。brainstorm 檔中的 `file:line`、rust 型別、TOML 欄名、`throttle_key` 等一律未帶入 spec；資料實體以「來源位址規則／信任模型設定／請求上下文」等業務語彙表述。**通過**。
- **可測試性**：46 條 FR 皆對應可觀察的系統行為；模糊詞（「妥善」「合理」）未使用。降級行為以「偏向放行／保留舊值／發告警」的可驗證方式表述。**通過**。
- **SC 可量測且技術中性**：12 條 SC 皆為使用者／維運可觀察的結果（時間、比率、100%、5 秒收斂），無框架或資料庫指標。**通過**。
- **邊界清楚**：FR-042~046 明列 MUST NOT；「假設」節區分「未實測承重前提」「有意識取捨」「環境驗收」「既有資產」「治理相依」五類。**通過**。
- **[NEEDS CLARIFICATION]**：零。三處會影響設計的懸空點（DNAT 前提、地理欄值形制、刪除端點動詞衝突）皆非「規格語意不明」而是「plan 階段的實作拍板題」，已在「假設／治理」節顯式標記為 plan 拍板，不以 clarification marker 呈現（符合「有合理預設或屬下游決策則不標記」原則）。**通過**。
- **可能的 analyze 假衝突預防**：FR-030 已顯式釐清「既有『判定不得依賴來源 IP』條文的射程＝帳號維度判定鍵」，避免 `/speckit-analyze` 將本刀的來源維度並列判定誤判為違反 007 FR-001。

首輪全通過，無需迭代。

### clarify 後重驗（2026-07-11）

兩個 clarification 折入後，「Requirements are testable and unambiguous」與「Scope is clearly bounded」兩項的支撐更強（原本 FR-026 的位址粒度、FR-033 的預設維度屬 Partial，現已明確）：
- **IPv6 節流粒度**：FR-026 明定 IPv4 /32、IPv6 /64；SC-006b 綁可量測結果；US4-6 與 Edge Cases 同步。消除了「per-IP 對 IPv6 是否有效」的高 impact 歧義。
- **手動解鎖預設維度**：FR-033 明定未指明＝帳號維（向後相容）；US4-7、Edge Cases、治理節 wire 契約句同步。契約案覆蓋兩案（analyze remediation 後 FR-033 擴來源標的欄、行為案擴為三案：未帶維度／顯式來源維帶來源標的／非法維度值）。

全 16 項維持通過（16/16 → 16/16）。三個 plan 拍板題（DNAT 前提、地理欄值形制、刪除端點動詞衝突）維持 defer 至 plan，非規格歧義。
