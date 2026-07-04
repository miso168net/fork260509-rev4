---
id: "0027"
title: 第一功能刀最小授權骨架——require_policy casbin enforce＋enforce_mw 骨架、登入延 auth 刀
date: 2026-07-05
status: accepted
supersedes: []
superseded_by: []
provenance: "rev4:2026-07-05 004-system-settings brainstorm 問答（拍板 4/7）"
tags: [authz, foundation, seam]
---

## 背景

system-settings（波 1 第一功能刀、ADR 0008）為 super-only，enforce 需呼叫者身分/角色
（Claims）→ 來自 JWT/登入。但登入是另一把 auth 刀（B-008、連「做真/stub/砍」都未拍）。
casbin policy 已 seed（002、R_SUPER 讀寫）、casbin adapter 已 vendored（002），但無身分源
就無法真 enforce。ADR 0008 要第一刀打通「授權」——需在無登入下先立授權骨架。

## 決定

- 第一刀建**最小授權骨架**：
  - **`require_policy(path, method)`**：DB-fresh roles → casbin enforce（已 seed policy）→
    deny → `5003`（`AppError::PermissionDenied`）。
  - **`enforce_mw` 骨架**：JWT decode → 注入 `Claims` 的接點；**JWT 簽發／登入端點不在本刀、
    留 auth 刀**。
- 測試以注入的 super `Claims` / 手工 test token（同 JWT secret 簽）驗授權管線通：super 過、
  非 super → `5003`。
- auth 刀（後來）接續完成 `enforce_mw` 的真 JWT 驗證＋登入端點簽發；本 seam 形狀為其接續依據，
  避免重造授權層。

## 後果

- 授權「檢查」骨架就位可測（ADR 0008「骨架先定形」達成）；身分源（登入）後補、非本刀 blast radius。
- auth 刀有明確接續契約（`enforce_mw` seam＋`require_policy` 形）。
- ★生產路徑限制：在 auth 刀落地登入前，這些端點對真實使用者不可達（無登入＝無真 token）；
  本刀前端亦因動態路由需 auth 而僅達碼/build/契約/單元驗（004 brainstorm 拍板 7）。
