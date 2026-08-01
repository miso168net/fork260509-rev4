# Specification Quality Checklist: 020-email-verify-smtp 帳號 email 驗證＋SMTP 寄信基建

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-07-31
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

- 「No implementation details」判定沿 015 先例口徑：FR／SC 本體維持行為級（「快取基建」「收信服務」
  「部署級靜態設定」等中性措辭）；具體選型（lettre 0.11.22、mailpit v1.30.6、SOPS、m014）僅出現於
  Clarifications（user 拍板記錄之忠實摘錄）與 Assumptions（既有資產／治理），屬 brainstorm 拍板的
  溯源載體、非規格對實作的指定。
- 零 [NEEDS CLARIFICATION]：九題拍板已覆蓋 scope／安全／UX 全部關鍵決策；餘下細節（表名逐字、
  信件文案、mailpit 網路路徑等）屬 plan 級、已列 brainstorm §4 留題與 spec 工程自拍清單（審 spec
  可翻案）。
- specify 驗證期三處校正（三語補正／admin 唯一拒因措辭／backend.* 鍵形）已寫入 Clarifications
  第二節，與 brainstorm 原文的偏差有明文溯源。
